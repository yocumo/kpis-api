CREATE OR REPLACE FUNCTION calculate_kpi_rows()
RETURNS TRIGGER AS $$
DECLARE
    v_calculated_etl NUMERIC := 0;
    v_calculated_etr NUMERIC := 0;
    v_calculated_ts NUMERIC := NULL;
    v_calculated_vr NUMERIC := 0;
    v_calculated_esi NUMERIC := 0;
    v_total NUMERIC := 0;
BEGIN
    -- Validate input data
    IF NEW.month IS NULL OR NEW.service_type_name IS NULL THEN
        RAISE EXCEPTION 'Invalid input: month and service_type_name are required';
    END IF;

    -- Optimize calculation using CTEs and simplified queries
    WITH task_summary AS (
        SELECT 
            t.service_type,
            t.request_activity,
            t.status,
            e.monthh,
            e.compliance_etl_etr,
            e.vr,
            e.esi,
            e.catv_test,
            e.esi_catv_test
        FROM tasks t
        JOIN estimateds e ON t.id = e.task_id
        WHERE e.monthh = NEW.month 
          AND t.service_type = NEW.service_type_name
    ),
    etl_calculation AS (
        SELECT 
            COALESCE(
                CASE 
                    WHEN COUNT(CASE WHEN status = 'Completada' AND request_activity = 'PROGRAMADA' THEN 1 END) > 0
                    THEN COUNT(CASE WHEN compliance_etl_etr = 'CUMPLE' AND request_activity = 'PROGRAMADA' THEN 1 END)::NUMERIC / 
                         COUNT(CASE WHEN status = 'Completada' AND request_activity = 'PROGRAMADA' THEN 1 END)
                    ELSE 0 
                END, 
                0
            ) AS etl_rate
        FROM task_summary
    ),
    etr_calculation AS (
        SELECT 
            COALESCE(
                CASE 
                    WHEN COUNT(CASE WHEN status = 'Completada' AND request_activity = 'INMEDIATA' THEN 1 END) > 0
                    THEN COUNT(CASE WHEN compliance_etl_etr = 'CUMPLE' AND request_activity = 'INMEDIATA' THEN 1 END)::NUMERIC / 
                         COUNT(CASE WHEN status = 'Completada' AND request_activity = 'INMEDIATA' THEN 1 END)
                    ELSE 0 
                END, 
                0
            ) AS etr_rate
        FROM task_summary
    ),
    vr_calculation AS (
        SELECT 
            1 - COALESCE(
                CASE 
                    WHEN COUNT(CASE WHEN catv_test >= 0 THEN 1 END) > 0
                    THEN COUNT(CASE WHEN vr = 'RECURRENTE' THEN 1 END)::NUMERIC / 
                         COUNT(CASE WHEN catv_test >= 0 THEN 1 END)
                    ELSE 0 
                END, 
                0
            ) AS vr_rate
        FROM task_summary
    ),
    esi_calculation AS (
        SELECT 
            1 - COALESCE(
                CASE 
                    WHEN COUNT(CASE WHEN esi_catv_test ~ '^-?\d+(\.\d+)?$' THEN 1 END) > 0
                    THEN COUNT(CASE WHEN esi = 'REINCIDENTE' THEN 1 END)::NUMERIC / 
                         COUNT(CASE WHEN esi_catv_test ~ '^-?\d+(\.\d+)?$' THEN 1 END)
                    ELSE 0 
                END, 
                0
            ) AS esi_rate
        FROM task_summary
    )
    SELECT 
        COALESCE(etl_rate, 0),
        COALESCE(etr_rate, 0),
        COALESCE(vr_rate, 0),
        COALESCE(esi_rate, 0)
    INTO 
        v_calculated_etl,
        v_calculated_etr,
        v_calculated_vr,
        v_calculated_esi
    FROM etl_calculation, etr_calculation, vr_calculation, esi_calculation;

    -- Calculate total with initial values
    v_total := COALESCE(v_calculated_etl, 0) + 
               COALESCE(v_calculated_etr, 0) + 
               COALESCE(v_calculated_ts, 0) + 
               COALESCE(v_calculated_vr, 0) + 
               COALESCE(v_calculated_esi, 0) + 
               100 + 95 + 100;

    -- Insert calculated data row
    INSERT INTO history_indicators (
        month, 
        service_type_name,
        row_type,
        etl,
        etr,
        ts,
        vr,
        esi,
        efo,
        cd,
        etci,
        total
    ) VALUES (
        NEW.month,
        NEW.service_type_name,
        'CALCULATED',
        v_calculated_etl,
        v_calculated_etr,
        v_calculated_ts,
        v_calculated_vr,
        v_calculated_esi,
        100,  -- Initial EFO
        95,   -- Initial CD
        100,  -- Initial ETCI
        v_total
    );

    -- Insert result row (multiplication)
    INSERT INTO history_indicators (
        month, 
        service_type_name,
        row_type,
        etl,
        etr,
        ts,
        vr,
        esi,
        efo,
        cd,
        etci,
        total
    ) VALUES (
        NEW.month,
        NEW.service_type_name,
        'RESULT',
        NEW.etl * v_calculated_etl,
        NEW.etr * v_calculated_etr,
        COALESCE(NEW.ts * v_calculated_ts, 0),
        NEW.vr * v_calculated_vr,
        NEW.esi * v_calculated_esi,
        NEW.efo * 100,
        NEW.cd * 95,
        NEW.etci * 100,
        NEW.total * v_total
    );

    RETURN NEW;
EXCEPTION 
    WHEN OTHERS THEN
        RAISE NOTICE 'Error in KPI calculation: %', SQLERRM;
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Recreate the trigger with additional checks
CREATE OR REPLACE TRIGGER kpi_calculation_trigger 
AFTER INSERT ON history_indicators 
FOR EACH ROW 
WHEN (NEW.month IS NOT NULL AND NEW.service_type_name IS NOT NULL)
EXECUTE FUNCTION calculate_kpi_rows();