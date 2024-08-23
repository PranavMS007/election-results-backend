CREATE DATABASE election_db;
CREATE TABLE IF NOT EXISTS public.constituency_results
(
    id serial NOT NULL,
    constituency varchar,
    party varchar,
    votes varchar,
    percentage float,
    CONSTRAINT constituency_results_pkey PRIMARY KEY (id)
);