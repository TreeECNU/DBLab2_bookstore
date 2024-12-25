--
-- PostgreSQL database dump
--

-- Dumped from database version 14.13
-- Dumped by pg_dump version 14.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: books; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.books (
    id text NOT NULL,
    title text,
    author text,
    publisher text,
    original_title text,
    translator text,
    pub_year text,
    pages integer,
    price real,
    currency_unit text,
    binding text,
    isbn text,
    author_intro text,
    book_intro text,
    content text,
    tags text
);


ALTER TABLE public.books OWNER TO postgres;

--
-- Name: new_order_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.new_order_details (
    order_id text NOT NULL,
    book_id text NOT NULL,
    count integer,
    price integer
);


ALTER TABLE public.new_order_details OWNER TO postgres;

--
-- Name: new_orders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.new_orders (
    order_id text NOT NULL,
    user_id text,
    store_id text,
    is_paid boolean,
    is_shipped boolean,
    is_received boolean,
    order_completed boolean,
    status text,
    created_time text
);


ALTER TABLE public.new_orders OWNER TO postgres;

--
-- Name: stores; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.stores (
    store_id text NOT NULL,
    book_id text NOT NULL,
    book_info text,
    stock_level integer
);


ALTER TABLE public.stores OWNER TO postgres;

--
-- Name: user_store; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_store (
    user_id text NOT NULL,
    store_id text NOT NULL
);


ALTER TABLE public.user_store OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id text NOT NULL,
    password text NOT NULL,
    balance integer NOT NULL,
    token text,
    terminal text
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: books books_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.books
    ADD CONSTRAINT books_pkey PRIMARY KEY (id);


--
-- Name: new_order_details new_order_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.new_order_details
    ADD CONSTRAINT new_order_details_pkey PRIMARY KEY (order_id, book_id);


--
-- Name: new_orders new_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.new_orders
    ADD CONSTRAINT new_orders_pkey PRIMARY KEY (order_id);


--
-- Name: stores stores_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stores
    ADD CONSTRAINT stores_pkey PRIMARY KEY (store_id, book_id);


--
-- Name: user_store user_store_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_store
    ADD CONSTRAINT user_store_pkey PRIMARY KEY (user_id, store_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- PostgreSQL database dump complete
--

