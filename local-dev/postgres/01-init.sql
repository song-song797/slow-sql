CREATE TABLE IF NOT EXISTS public.xxl_job_log (
    id BIGINT PRIMARY KEY,
    job_group INTEGER,
    job_id BIGINT,
    executor_address TEXT,
    trigger_code INTEGER,
    handle_code INTEGER,
    alarm_status INTEGER,
    trigger_time TIMESTAMP,
    handle_time TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.xxl_job_log_report (
    trigger_day DATE PRIMARY KEY,
    running_count INTEGER,
    suc_count INTEGER,
    fail_count INTEGER
);

CREATE TABLE IF NOT EXISTS public.xxl_job_info (
    id BIGINT PRIMARY KEY,
    job_group INTEGER,
    job_desc TEXT,
    add_time TIMESTAMP,
    update_time TIMESTAMP,
    author TEXT,
    alarm_email TEXT,
    schedule_type TEXT,
    schedule_conf TEXT,
    misfire_strategy TEXT,
    executor_route_strategy TEXT,
    executor_handler TEXT,
    executor_param TEXT,
    executor_block_strategy TEXT,
    executor_timeout INTEGER,
    executor_fail_retry_count INTEGER,
    glue_type TEXT,
    glue_source TEXT,
    glue_remark TEXT,
    glue_updatetime TIMESTAMP,
    child_jobid TEXT,
    trigger_status INTEGER,
    trigger_last_time BIGINT,
    trigger_next_time BIGINT
);

CREATE TABLE IF NOT EXISTS public.xxl_job_lock (
    lock_name TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS public.roles (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    role TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS public.permissions (
    id BIGSERIAL PRIMARY KEY,
    role TEXT NOT NULL,
    permission TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS public.users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.config_info_beta (
    id BIGINT PRIMARY KEY,
    data_id TEXT,
    group_id TEXT,
    content TEXT,
    md5 TEXT,
    gmt_create TIMESTAMP,
    gmt_modified TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_xxl_job_log_trigger_time ON public.xxl_job_log (trigger_time);
CREATE INDEX IF NOT EXISTS idx_xxl_job_log_alarm_status ON public.xxl_job_log (alarm_status);
CREATE INDEX IF NOT EXISTS idx_xxl_job_info_trigger_status ON public.xxl_job_info (trigger_status);
CREATE INDEX IF NOT EXISTS idx_roles_username ON public.roles (username);
CREATE INDEX IF NOT EXISTS idx_permissions_role ON public.permissions (role);
CREATE INDEX IF NOT EXISTS idx_users_username ON public.users (username);

INSERT INTO public.xxl_job_lock (lock_name)
VALUES ('schedule_lock')
ON CONFLICT (lock_name) DO NOTHING;

INSERT INTO public.roles (username, role)
VALUES
    ('demo-admin', 'admin'),
    ('demo-user', 'user')
ON CONFLICT DO NOTHING;

INSERT INTO public.permissions (role, permission)
VALUES
    ('admin', 'system:manage'),
    ('user', 'system:view')
ON CONFLICT DO NOTHING;

INSERT INTO public.users (username, password)
VALUES
    ('demo-admin', 'demo-password'),
    ('demo-user', 'demo-password')
ON CONFLICT DO NOTHING;

INSERT INTO public.config_info_beta (id, data_id, group_id, content, md5, gmt_create, gmt_modified)
VALUES (1, 'demo-config', 'DEFAULT_GROUP', '{\"enabled\":true}', 'demo-md5', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (id) DO NOTHING;
