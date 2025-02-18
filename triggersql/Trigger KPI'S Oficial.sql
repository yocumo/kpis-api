CREATE OR REPLACE FUNCTION calculate_estimated_times()
    RETURNS trigger AS $$
DECLARE
    programada_minutes numeric;
    inmediata_minutes numeric;
    calculated_time timestamp;
    compliance_result varchar;
    arrival_dead_minutes numeric;
    adjusted_arrival_time timestamp;
    confirmation_waiting_interval interval;
    confirmation_waiting_minutes integer;
    confirmation_waiting_time interval;
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
    vr_date_result timestamp;
    vr_staff_result varchar;
    vr_result varchar;
    days_between numeric;
    one_fifty_result numeric;
    esi_date_result timestamp;
    esi_catv_test_result integer;
    esi_staff_result varchar;
    root_cause_ant_result varchar;
    esi_result varchar;
    days_betweenn numeric;
    catv_count integer;
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
        calculated_time := NEW.scheduled_time AT TIME ZONE 'UTC' - 
                        (programada_minutes * interval '1 minute');
        calculated_time := date_trunc('minute', calculated_time);
        
    ELSIF NEW.request_activity = 'INMEDIATA' AND NEW.status = 'Completada' THEN
        calculated_time := NEW.date_delivery_time AT TIME ZONE 'UTC' + 
                        (inmediata_minutes * interval '1 minute');
        calculated_time := date_trunc('minute', calculated_time);
    ELSE
        calculated_time := NULL;
    END IF;
    --TODO:: Calcular CUMPLIMIENTO ETL/ETR
   

    IF NEW.arrival_time IS NULL OR calculated_time IS NULL THEN
        compliance_result := '';
    ELSE
        -- Restar el tiempo muerto de llegada a la hora de llegada
        -- IF (NEW.arrival_time - (NEW.arrival_dead_time || ' minutes')::interval) <= calculated_time THEN
        --     compliance_result := 'CUMPLE';
        -- ELSE
        --     compliance_result := 'NO CUMPLE';
        -- END IF;
        arrival_dead_minutes := COALESCE((EXTRACT(HOUR FROM NEW.arrival_dead_time::interval) * 60) + 
         EXTRACT(MINUTE FROM NEW.arrival_dead_time::interval),0);
        adjusted_arrival_time := NEW.arrival_time - (arrival_dead_minutes * interval '1 minute'); 

        IF adjusted_arrival_time <= calculated_time THEN
            compliance_result := 'CUMPLE';
        ELSE
            compliance_result := 'NO CUMPLE';
        END IF;
    END IF;
    
    --TODO:: Calcular TIEMPO ESPERA CONFIRMACIÓN
    IF NEW.confirmation_time IS NOT NULL AND NEW.final_time IS NOT NULL 
        AND NEW.confirmation_time > NEW.final_time THEN
        confirmation_waiting_interval := NEW.confirmation_time - NEW.final_time;
        confirmation_waiting_minutes := EXTRACT(EPOCH FROM confirmation_waiting_interval)::integer;
    ELSE
        confirmation_waiting_time := 0;
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

  -- TODO::Cálculo de ESI_CATV_TEST
    IF NEW.status <> 'Completada' THEN
        esi_catv_test_result := NULL;
    ELSE
        IF EXISTS (
            SELECT 1 
            FROM exceptions_cavid 
            WHERE cavid = NEW.cav_id
        ) OR NEW.attributable = '0' 
        OR NEW.attributable = 'CLIENTE' THEN
            esi_catv_test_result := 0;
        ELSE
            -- Contar tareas que cumplan las condiciones
            SELECT COUNT(*)
            INTO esi_catv_test_result
            FROM tasks 
            WHERE cav_id = NEW.cav_id 
            AND status = NEW.status
            AND attributable = NEW.attributable;
        END IF;
    END IF;
    
    --- TODO:: CATV_TEST
    IF NEW.status <> 'Completada' THEN
       catv_count := NULL; 
    ELSIF (SELECT COUNT(*) FROM exceptions_cavid WHERE cavid = NEW.cav_id LIMIT 1) > 0 AND 
    (NEW.attributable = '0' OR NEW.attributable = 'CLIENTE') THEN
       catv_count := 0; 
        ELSE
            SELECT COUNT(*)
            INTO catv_count
            FROM tasks
            WHERE cav_id = NEW.cav_id 
            AND status = NEW.status 
            AND attributable = NEW.attributable;
    END IF;
       -- TODO:: Cálculo de ROOT_CAUSE_ANT
    IF NEW.cav_id = 'N/A' OR NEW.cav_id ='N/a'
       OR NEW.root_cause = '0' 
       OR NEW.status <> 'Completada' THEN
        root_cause_ant_result := NULL;
    ELSE
        -- Buscar la causa raíz de la última tarea que cumpla las condiciones
        SELECT root_cause
        INTO root_cause_ant_result
        FROM tasks 
        WHERE cav_id = NEW.cav_id 
        AND status = NEW.status
        AND root_cause = NEW.root_cause
        AND attributable = 'ETB'
        AND id <> NEW.id  -- Excluir la tarea actual
        ORDER BY final_time DESC
        LIMIT 1;
    END IF;

-- TODO:: Cálculo de ESI_DATE
    IF NEW.status <> 'Completada' THEN
        esi_date_result := NULL;
    ELSE
        -- Verificar si el CAV/ID existe en excepciones o si es atribuible a cliente o causa raíz es 0
        IF EXISTS (
            SELECT 1
            FROM exceptions_cavid 
            WHERE cavid = NEW.cav_id
        ) OR NEW.attributable = '0' 
        OR NEW.attributable = 'CLIENTE'
        OR NEW.root_cause = '0' THEN
            esi_date_result := NULL;
        ELSE
            -- Buscar la fecha de la última tarea que cumpla las condiciones
            SELECT final_time 
            INTO esi_date_result
            FROM tasks 
            WHERE cav_id = NEW.cav_id 
            AND status = 'Completada'
            AND root_cause = NEW.root_cause
            AND attributable = 'ETB'
            AND id <> NEW.id  -- Excluir la tarea actual
            ORDER BY final_time DESC
            LIMIT 1;
        END IF;
    END IF;
    -- TODO:: Cálculo de ESI
    IF NEW.status != 'Completada' THEN
        esi_result := NULL;
    ELSE
        -- Validamos casos donde el resultado es NO REINCIDENTE
        IF NEW.resolutioncategory_2ps = 'VISITA FALLIDA' OR 
        NEW.resolutioncategory_2ps = 'VISITA CANCELADA' OR
        NEW.confirmation_time IS NULL OR
        NEW.root_cause IS NULL OR
        esi_catv_test_result IS NULL THEN
            esi_result := 'NO REINCIDENTE';
        ELSE
            -- Calcular la diferencia en días entre confirmation_time y esi_date
            days_betweenn := EXTRACT(EPOCH FROM (NEW.confirmation_time - esi_date_result)) / (24 * 60 * 60);
            
            -- Verificar las condiciones para REINCIDENTE
            IF (
                -- Primera condición
                (esi_catv_test_result > 1 AND 
                NEW.root_cause = root_cause_ant_result AND 
                days_betweenn <= 30)
                OR
                -- Segunda condición
                (days_betweenn <= 60 AND days_betweenn > 30)
            ) THEN
                esi_result := 'REINCIDENTE';
            ELSE
                esi_result := 'NO REINCIDENTE';
            END IF;
        END IF;
    END IF;
    
    
  
    -- TODO::Cálculo de ESI_STAFF
    IF NEW.status <> 'Completada' THEN
        esi_staff_result := NULL;
    ELSE
        IF EXISTS (
            SELECT 1 
            FROM exceptions_cavid 
            WHERE cavid = NEW.cav_id
        ) OR NEW.attributable = '0' 
        OR NEW.attributable = 'CLIENTE' THEN
            esi_staff_result := NULL;
        ELSE
            -- Buscar el técnico de la última tarea que cumpla las condiciones
            SELECT assigned_staff
            INTO esi_staff_result
            FROM tasks 
            WHERE cav_id = NEW.cav_id 
            AND status = NEW.status
            AND attributable = 'ETB'
            AND id <> NEW.id  -- Excluir la tarea actual
            ORDER BY final_time DESC
            LIMIT 1;
        END IF;
    END IF;
 
    
    -- TODO:: Nuevo cálculo para FECHA VR VR_DATE
    IF NEW.status <> 'Completada' THEN
        vr_date_result := NULL;
    ELSE
        -- Verificar si el CAV/ID existe en excepciones o si es atribuible a cliente
        IF EXISTS (
            SELECT 1 
            FROM exceptions_cavid 
            WHERE cavid = NEW.cav_id
        ) OR NEW.attributable = '0' 
        OR NEW.attributable = 'CLIENTE' THEN
            vr_date_result := NULL;
        ELSE
            -- Buscar la última tarea completada para el mismo CAV/ID atribuible a ETB
            SELECT final_time 
            INTO vr_date_result
            FROM tasks 
            WHERE cav_id = NEW.cav_id 
            AND status = 'Completada'
            AND attributable = 'ETB'
            AND id <> NEW.id  -- Excluir la tarea actual
            ORDER BY final_time DESC
            LIMIT 1;
        END IF;
    END IF;
-- TODO:: para TECNICOS VR - VR_STAFF
    IF NEW.status <> 'Completada' THEN
        vr_staff_result := NULL;
    ELSE
        IF EXISTS (
            SELECT 1 
            FROM exceptions_cavid 
            WHERE cavid = NEW.cav_id
        ) OR NEW.attributable = '0' 
        OR NEW.attributable = 'CLIENTE' THEN
            vr_staff_result := NULL;
        ELSE
            -- Buscar el técnico de la última tarea completada para el mismo CAV/ID atribuible a ETB
            SELECT assigned_staff
            INTO vr_staff_result
            FROM tasks 
            WHERE cav_id = NEW.cav_id 
            AND status = 'Completada'
            AND attributable = 'ETB'
            AND id <> NEW.id
            ORDER BY final_time DESC
            LIMIT 1;
        END IF;
    END IF;
    -- TODO:: Cálculo para VR
    IF vr_date_result IS NULL OR 
       NEW.resolutioncategory_2ps = 'VISITA FALLIDA' OR 
       NEW.resolutioncategory_2ps = 'VISITA CANCELADA' THEN
        vr_result := '';
    ELSE
        -- Calcular la diferencia en días entre confirmation_time y vr_date
        IF NEW.confirmation_time IS NOT NULL THEN
            days_between := EXTRACT(EPOCH FROM (NEW.confirmation_time - vr_date_result)) / (24 * 60 * 60);
            
            IF days_between <= 30 AND 
               EXISTS (
                   SELECT 1 
                   FROM estimateds 
                   WHERE task_id = NEW.id 
                   AND catv_test > 0 
                   AND (esi IS NULL OR esi <> 'REINCIDENTE')
               ) THEN
                vr_result := 'RECURRENTE';
            ELSE
                vr_result := 'NO RECURRENTE';
            END IF;
        ELSE
            vr_result := '';
        END IF;
    END IF;
    ---TODO:: TS
     -- Convertir el tiempo total a horas para la comparación
    -- total_time_hours := EXTRACT(EPOCH FROM total_time_interval) / 3600;  
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
			)) / 3600 INTO max_hours_for_category;
            IF CEIL(total_time_hours * 60) <= CEIL(max_hours_for_category * 60) THEN
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
    -- Todo::Cálculo de one_fifty
    one_fifty_result := 
        EXTRACT(EPOCH FROM total_time_interval)/60 +
        COALESCE(EXTRACT(EPOCH FROM NEW.arrival_dead_time)/60, 0) +
        COALESCE(EXTRACT(EPOCH FROM NEW.execution_dead_time)/60, 0);
        
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
        ts,
        vr_date,
        vr_staff,
        vr,
        one_fifty,
        esi_date,
        esi_catv_test,
        esi_staff,
        root_cause_ant,
        esi,
        catv_test
    )
    VALUES (
        NEW.id,
        CASE 
            WHEN calculated_time IS NOT NULL THEN to_char(calculated_time AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI')
            ELSE NULL 
        END,
        compliance_result,
        COALESCE(to_char((confirmation_waiting_minutes * interval '1 second'), 'HH24:MI:SS'), '00:00:00')::time,
        COALESCE(to_char((total_time_minutes || ' minutes')::interval, 'HH24:MI'), '00:00')::time,
		day_week,
        dead_time,
        dayy,
        time_int,
        monthh,
        days_recurrence,
        ts_status,
        vr_date_result,
        vr_staff_result,
        vr_result,
        one_fifty_result,
        esi_date_result,
        esi_catv_test_result,
        esi_staff_result,
        root_cause_ant_result,
        esi_result,
        catv_count
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
        vr_date = EXCLUDED.vr_date,
        vr_staff = EXCLUDED.vr_staff,
        vr = EXCLUDED.vr,
        one_fifty = EXCLUDED.one_fifty,
        esi_date = EXCLUDED.esi_date,
        esi_catv_test = EXCLUDED.esi_catv_test,
        esi_staff = EXCLUDED.esi_staff,
        root_cause_ant = EXCLUDED.root_cause_ant,
        esi = EXCLUDED.esi,
        catv_test = EXCLUDED.catv_test,
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql
;

DROP TRIGGER IF EXISTS trigger_calculate_estimated_times ON tasks;

CREATE TRIGGER trigger_calculate_estimated_times AFTER
INSERT
    OR
UPDATE ON tasks FOR EACH ROW
EXECUTE FUNCTION calculate_estimated_times ();