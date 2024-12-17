## TODO:: ETL
SELECT t.service_type, t.request_activity, t.status, e.monthh, e.compliance_etl_etr, e.vr, e.esi, e.catv_test, e.esi_catv_test
FROM tasks t
    JOIN estimateds e ON t.id = e.task_id
WHERE
    e.monthh = 12
    AND t.service_type = 'ASG_CUM_01';

-- Cálculo de KPIs de ETL
WITH
    filtered_tasks AS (
        SELECT *
        FROM tasks t
            JOIN estimateds e ON t.id = e.task_id
        WHERE
            e.monthh = 12
            AND t.service_type = 'ASG_CUM_01'
            AND t.status = 'Completada'
            AND t.request_activity = 'PROGRAMADA'
    )

SELECT
    COUNT(*) AS etl_total,
    COUNT(
        CASE
            WHEN compliance_etl_etr = 'CUMPLE' THEN 1
        END
    ) AS etl_cumple,
    COALESCE(
        COUNT(
            CASE
                WHEN compliance_etl_etr = 'CUMPLE' THEN 1
            END
        ) * 100.0 / NULLIF(COUNT(*), 0),
        0
    ) AS etl_rate
FROM filtered_tasks;

## TODO:: ETR
SELECT t.service_type, t.request_activity, t.status, e.monthh, e.compliance_etl_etr, e.vr, e.esi, e.catv_test, e.esi_catv_test
FROM tasks t
    JOIN estimateds e ON t.id = e.task_id
WHERE
    e.monthh = 12
    AND t.service_type = 'ASG_CUM_01';

-- Cálculo de KPIs de ETL
WITH
    filtered_tasks AS (
        SELECT *
        FROM tasks t
            JOIN estimateds e ON t.id = e.task_id
        WHERE
            e.monthh = 12
            AND t.service_type = 'ASG_CUM_01'
            AND t.status = 'Completada'
            AND t.request_activity = 'INMEDIATA'
    )

SELECT
    COUNT(*) AS etl_total,
    COUNT(
        CASE
            WHEN compliance_etl_etr = 'CUMPLE' THEN 1
        END
    ) AS etl_cumple,
    COALESCE(
        COUNT(
            CASE
                WHEN compliance_etl_etr = 'CUMPLE' THEN 1
            END
        ) * 100.0 / NULLIF(COUNT(*), 0),
        0
    ) AS etl_rate
FROM filtered_tasks;

### TODO:: ES
WITH
    filtered_tasks AS (
        SELECT ts
        FROM estimateds e
            JOIN tasks t ON t.id = e.task_id
        WHERE
            e.monthh = 12
            AND t.service_type = 'ASG_CUM_01'
    )

SELECT
    COUNT(
        CASE
            WHEN ts = 'CUMPLE' THEN 1
        END
    ) AS cumple_count,
    COUNT(
        CASE
            WHEN ts = 'NO CUMPLE' THEN 1
        END
    ) AS no_cumple_count,
    ROUND(
        COUNT(
            CASE
                WHEN ts = 'CUMPLE' THEN 1
            END
        ) * 100.0 / NULLIF(
            COUNT(
                CASE
                    WHEN ts = 'CUMPLE' THEN 1
                END
            ) + COUNT(
                CASE
                    WHEN ts = 'NO CUMPLE' THEN 1
                END
            ),
            0
        ),
        2
    ) AS ts_rate_porcentaje
FROM filtered_tasks;