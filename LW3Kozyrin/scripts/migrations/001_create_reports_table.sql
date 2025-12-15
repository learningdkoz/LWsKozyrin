-- Миграция для создания таблицы reports
-- Дата создания: 2024
-- Описание: Таблица для хранения ежедневных отчетов по заказам

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    report_at DATE NOT NULL,
    order_id INTEGER NOT NULL,
    count_product INTEGER NOT NULL,
    CONSTRAINT fk_reports_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- Создаем индекс по дате для быстрого поиска отчетов
CREATE INDEX IF NOT EXISTS idx_reports_report_at ON reports(report_at);

-- Создаем индекс по order_id для связи с заказами
CREATE INDEX IF NOT EXISTS idx_reports_order_id ON reports(order_id);

-- Комментарии к таблице и колонкам
COMMENT ON TABLE reports IS 'Таблица для хранения ежедневных отчетов по заказам';
COMMENT ON COLUMN reports.id IS 'Уникальный идентификатор отчета';
COMMENT ON COLUMN reports.report_at IS 'Дата, за которую сформирован отчет';
COMMENT ON COLUMN reports.order_id IS 'ID заказа, по которому сформирован отчет';
COMMENT ON COLUMN reports.count_product IS 'Общее количество продуктов в заказе';
