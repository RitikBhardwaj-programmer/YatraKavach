-- YatraKavach shared schema. Contract: docs/PLAN.md. Workstreams add files 010-019 (hazard) and 020-029 (alerts).
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE segments (
    id                 text PRIMARY KEY,           -- e.g. VD-OLD-01
    route_id           text NOT NULL,
    route_name         text NOT NULL,
    seq                int  NOT NULL,
    geom               geometry(LineString, 4326) NOT NULL,
    length_m           real NOT NULL,
    width_m            real NOT NULL,
    kind               text NOT NULL DEFAULT 'trail' CHECK (kind IN ('trail', 'junction', 'bridge', 'nala', 'camp')),
    landmark           text,
    elev_m             real,
    terrain_slope_deg  real,
    grade_deg          real,
    susceptibility     smallint CHECK (susceptibility BETWEEN 1 AND 4),  -- GSI class if available, else NULL
    past_slide         boolean NOT NULL DEFAULT false,
    rain_point         text NOT NULL                -- katra | adhkuwari | bhawan
);
CREATE INDEX segments_geom_idx ON segments USING gist (geom);

CREATE TABLE rain_hourly (
    point      text NOT NULL,
    ts         timestamptz NOT NULL,
    source     text NOT NULL,                       -- ecmwf_ifs025 | gfs_seamless | era5 | live model name
    mode       text NOT NULL CHECK (mode IN ('live', 'replay')),
    precip_mm  real NOT NULL,
    PRIMARY KEY (point, ts, source, mode)
);

CREATE TABLE segment_hazard (
    segment_id          text NOT NULL REFERENCES segments(id),
    ts                  timestamptz NOT NULL,
    mode                text NOT NULL CHECK (mode IN ('live', 'replay')),
    source              text NOT NULL,
    level               smallint NOT NULL CHECK (level BETWEEN 0 AND 3),
    drivers             jsonb NOT NULL,
    thresholds_version  text NOT NULL,
    PRIMARY KEY (segment_id, ts, mode, source)
);

CREATE TABLE segment_crowd (
    segment_id    text NOT NULL REFERENCES segments(id),
    ts            timestamptz NOT NULL,
    mode          text NOT NULL CHECK (mode IN ('live', 'replay')),
    persons       int  NOT NULL,
    density_ppm2  real NOT NULL,
    level         smallint NOT NULL CHECK (level BETWEEN 0 AND 3),
    simulated     boolean NOT NULL DEFAULT true,
    PRIMARY KEY (segment_id, ts, mode)
);

CREATE TABLE segment_risk (
    segment_id    text NOT NULL REFERENCES segments(id),
    ts            timestamptz NOT NULL,
    mode          text NOT NULL CHECK (mode IN ('live', 'replay')),
    source        text NOT NULL,
    hazard_level  smallint NOT NULL,
    crowd_level   smallint NOT NULL,
    risk_level    smallint NOT NULL CHECK (risk_level BETWEEN 0 AND 3),
    drivers       jsonb NOT NULL,
    PRIMARY KEY (segment_id, ts, mode, source)
);

CREATE TABLE officers (
    id    text PRIMARY KEY,
    name  text NOT NULL,
    role  text NOT NULL CHECK (role IN ('officer', 'senior'))
);
INSERT INTO officers (id, name, role) VALUES
    ('off-1', 'Demo Officer A (Katra control room)', 'officer'),
    ('off-2', 'Demo Officer B (SDRF liaison)', 'officer'),
    ('sen-1', 'Demo Senior Officer (Incident Commander)', 'senior');
