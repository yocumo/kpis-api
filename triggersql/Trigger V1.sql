CREATE OR REPLACE FUNCTION calculate_estimated_times()
    RETURNS trigger AS $$
DECLARE
    programada_minutes numeric;
    inmediata_minutes numeric;
    calculated_time timestamp;
    compliance_result varchar;
    confirmation_waiting_interval interval;
    confirmation_waiting_minutes integer;
    total_time_interval interval;
    total_time_minutes integer;
	day_week integer;
	dead_time numeric;
    dayy integer;
    monthh integer;
    time_int numeric;
    days_recurrence numeric;

    ts_status varchar(20) := '';
    max_hours_for_category numeric;
    total_time_hours numeric;
    operational_category_completable boolean;


BEGIN
    -- Obtenemos los minutos para actividad PROGRAMADA
    SELECT extract(hour from minut) * 60 + extract(minute from minut)
    INTO programada_minutes
    FROM exceptions_activity
    WHERE activity = 'PROGRAMADA';
    
    -- Obtenemos los minutos para actividad INMEDIATA
    SELECT extract(hour from minut) * 60 + extract(minute from minut)
    INTO inmediata_minutes
    FROM exceptions_activity
    WHERE activity = 'INMEDIATA';
    
    --TODO:: Aplicamos la lógica del IF de Excel para expected_current_date_time
    IF NEW.request_activity = 'PROGRAMADA' AND NEW.status = 'Completada' THEN
        calculated_time := date_trunc('minute', NEW.scheduled_time AT TIME ZONE 'UTC' - (programada_minutes || ' minutes')::interval);
    ELSIF NEW.request_activity = 'INMEDIATA' AND NEW.status = 'Completada' THEN
        calculated_time := date_trunc('minute', NEW.date_delivery_time AT TIME ZONE 'UTC' + (inmediata_minutes || ' minutes')::interval);
    ELSE
        calculated_time := NULL;
    END IF;
    --TODO:: Calcular CUMPLIMIENTO ETL/ETR
    IF NEW.arrival_time IS NULL OR calculated_time IS NULL THEN
        compliance_result := '';
    ELSE
        -- Restar el tiempo muerto de llegada a la hora de llegada
        IF (NEW.arrival_time - (NEW.arrival_dead_time || ' minutes')::interval) <= calculated_time THEN
            compliance_result := 'CUMPLE';
        ELSE
            compliance_result := 'NO CUMPLE';
        END IF;
    END IF;
    
    --TODO:: Calcular TIEMPO ESPERA CONFIRMACIÓN
    IF NEW.confirmation_time IS NOT NULL AND NEW.final_time IS NOT NULL 
       AND NEW.confirmation_time > NEW.final_time THEN
        confirmation_waiting_interval := NEW.confirmation_time - NEW.final_time;
        confirmation_waiting_minutes := EXTRACT(HOUR FROM confirmation_waiting_interval) * 60 + 
                                        EXTRACT(MINUTE FROM confirmation_waiting_interval);
    ELSE
        confirmation_waiting_minutes := 0;
    END IF;

    ---TODO:: Calcular Tiempo Total
    IF NEW.status <> 'Completada' THEN
        total_time_interval := '0 minutes';
        total_time_minutes := 0;
    ELSE
        IF NEW.request_activity = 'INMEDIATA' THEN
            total_time_interval := NEW.confirmation_time - NEW.date_delivery_time 
                                    - confirmation_waiting_interval 
                                    - (NEW.execution_dead_time || ' minutes')::interval 
                                    - (NEW.arrival_dead_time || ' minutes')::interval 
                                    - (NEW.customer_waiting || ' minutes')::interval;
        ELSE
            -- Para actividades PROGRAMADA
            total_time_interval := NEW.confirmation_time - NEW.scheduled_time 
                                    - confirmation_waiting_interval 
                                    - (NEW.execution_dead_time || ' minutes')::interval 
                                    - (NEW.arrival_dead_time || ' minutes')::interval;
            
            -- Si el resultado es negativo, se establece a 0
            IF total_time_interval < '0 minutes' THEN
                total_time_interval := '0 minutes';
            END IF;
        END IF;
        
        -- Calcular los minutos totales
        total_time_minutes := EXTRACT(HOUR FROM total_time_interval) * 60 + 
                               EXTRACT(MINUTE FROM total_time_interval);
    END IF;

     ---TODO:: TS
    IF NEW.resolutioncategory_2ps IN ('VISITA FALLIDA', 'VISITA CANCELADA') THEN
        ts_status := '';
	
    ELSE
        -- Check if the operational category is completable for the given status
        SELECT CASE 
            WHEN EXISTS (
                SELECT 1 
                FROM exceptions_category 
                WHERE category_type = NEW.operational_category 
                  AND category_type || 'Completada' = NEW.operational_category || NEW.status
            ) THEN true 
            ELSE false 
        END INTO operational_category_completable;

        IF operational_category_completable AND total_time_minutes >= 0 THEN
            SELECT EXTRACT(EPOCH FROM COALESCE(
			(SELECT hourr
			 FROM exceptions_category 
			 WHERE category_type = NEW.operational_category), 
			'00:00:00'::time
			)) INTO max_hours_for_category;

            total_time_hours := total_time_minutes / 60.0;

            IF total_time_hours <= max_hours_for_category THEN
                ts_status := 'CUMPLE';
            ELSE
                ts_status := 'NO CUMPLE';
            END IF;
        END IF;
    END IF;



    ---TODO:: DIAS RECURRENCIA
    IF NEW.arrival_time IS NULL THEN
        days_recurrence := NULL;
    ELSE
        days_recurrence := ROUND(EXTRACT(EPOCH FROM (CURRENT_DATE - NEW.arrival_time)) / (24 * 60 * 60));

    END IF;

    ---TODO:: MES
    IF NEW.arrival_time IS NULL THEN
        monthh := NULL;
    ELSE
        monthh := TO_CHAR(NEW.arrival_time, 'MM');
    END IF;

    ---TODO:: DIA
    IF NEW.arrival_time IS NULL THEN
        dayy := NULL;
    ELSE
        dayy := TO_CHAR(NEW.arrival_time, 'DD');
    END IF;

	  --TODO:: day_week
    IF New.scheduled_time IS NULL THEN
        day_week := NULL;
    ELSE
        IF New.request_activity = 'PROGRAMADA' THEN
            day_week := EXTRACT(DOW FROM NEW.scheduled_time);
        ELSE
            day_week := EXTRACT(DOW FROM NEW.date_delivery_time);
        END IF;

    END IF;

-- TODO:: HORA_INT
    IF NEW.request_activity = 'PROGRAMADA' THEN
        time_int:= ROUND(((EXTRACT(HOUR FROM NEW.scheduled_time) + 
                       EXTRACT(MINUTE FROM NEW.scheduled_time) / 60) * 2) / 2, 1);
    ELSE
        time_int:= ROUND(((EXTRACT(HOUR FROM NEW.date_delivery_time) + 
                       EXTRACT(MINUTE FROM NEW.date_delivery_time) / 60) * 2) / 2, 1);
    END IF;

    --TODO:: Tiempo Muerto
    IF NEW.arrival_time IS NOT NULL AND NEW.date_delivery_time IS NOT NULL THEN
        dead_time := CEIL((EXTRACT(EPOCH FROM NEW.arrival_time - NEW.date_delivery_time) / 3600) * 10) / 10;
    ELSE
        dead_time := NULL;
    END IF;

    -- Insertamos o actualizamos el registro en estimateds
    INSERT INTO estimateds (
        task_id,
        expected_current_date_time,
        compliance_etl_etr,
        confirmation_waiting_time,
        total_time,
		day_week,
        dead_time,
        dayy,
        time_int,
        monthh,
        days_recurrence,
        ts
    )
    VALUES (
        NEW.id,
        CASE 
            WHEN calculated_time IS NOT NULL THEN to_char(calculated_time AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI')
            ELSE NULL 
        END,
        compliance_result,
        COALESCE(to_char((confirmation_waiting_minutes * interval '1 minute'), 'HH24:MI'), '00:00')::time,
        COALESCE(to_char((total_time_minutes || ' minutes')::interval, 'HH24:MI'), '00:00')::time,
		day_week,
        dead_time,
        dayy,
        time_int,
        monthh,
        days_recurrence,
        ts_status
    )
    ON CONFLICT (task_id) DO UPDATE
    SET 
        expected_current_date_time = EXCLUDED.expected_current_date_time,
        compliance_etl_etr = EXCLUDED.compliance_etl_etr,
        confirmation_waiting_time = EXCLUDED.confirmation_waiting_time,
        total_time = EXCLUDED.total_time,
        day_week = EXCLUDED.day_week,
        dead_time = EXCLUDED.dead_time,
        dayy = EXCLUDED.dayy,
        time_int = EXCLUDED.time_int,
        monthh = EXCLUDED.monthh,
        days_recurrence = EXCLUDED.days_recurrence,
        ts = EXCLUDED.ts,
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_calculate_estimated_times ON tasks;

CREATE TRIGGER trigger_calculate_estimated_times AFTER
INSERT
    OR
UPDATE ON tasks FOR EACH ROW
EXECUTE FUNCTION calculate_estimated_times ();