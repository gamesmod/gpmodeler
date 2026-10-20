#!/bin/bash
# Интеграционная проверка: SQL, который gpModeler генерирует для Cloudberry/Greenplum,
# применяется на живом сервере, затем по каталогам проверяются политика распределения
# и параметры хранения таблиц.
#
# Использование: tests/cloudberry/run.sh <путь к gpmodeler-cli>
# Подключение берётся из PGHOST, PGPORT, PGUSER и PGPASSWORD
# (по умолчанию 127.0.0.1:5432, gpadmin).
set -euo pipefail

CLI="${1:?Укажите путь к gpmodeler-cli}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

export PGHOST="${PGHOST:-127.0.0.1}" PGPORT="${PGPORT:-5432}" PGUSER="${PGUSER:-gpadmin}"
DB="gpmodeler_test"
PSQL=(psql -v ON_ERROR_STOP=1 -q)

echo "== Экспорт модели в SQL"
"$CLI" --input "$DIR/cloudberry.dbm" --export-to-file --output "$WORK/model.sql"

# Базу создаёт сам скрипт, поэтому CREATE DATABASE из экспорта убираем
sed -i '/^CREATE DATABASE/d' "$WORK/model.sql"

echo "== Применение SQL на сервере"
"${PSQL[@]}" -d postgres -c "DROP DATABASE IF EXISTS $DB" -c "CREATE DATABASE $DB"
"${PSQL[@]}" -d "$DB" -f "$WORK/model.sql"

echo "== Проверка каталогов"
# policytype у Greenplum и Cloudberry различается, поэтому политику выводим по ключу:
# replicated - 'r', пустой ключ - случайное распределение, иначе хэш
"${PSQL[@]}" -d "$DB" -Atc "
  SELECT c.relname,
         CASE WHEN p.policytype = 'r' THEN 'replicated'
              WHEN p.distkey::text = '' THEN 'random'
              ELSE 'hash' END,
         p.distkey::text,
         am.amname,
         c.reloptions::text
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  LEFT JOIN gp_distribution_policy p ON p.localoid = c.oid
  LEFT JOIN pg_am am ON am.oid = c.relam
  WHERE n.nspname = 'mpp_test' AND c.relkind = 'r'
  ORDER BY 1" > "$WORK/actual.txt"

if diff -u "$DIR/expected.txt" "$WORK/actual.txt"; then
  echo "OK: распределение и хранение таблиц совпали с ожидаемыми"
else
  echo "ОШИБКА: каталоги сервера отличаются от ожидаемых (см. diff выше)" >&2
  exit 1
fi
