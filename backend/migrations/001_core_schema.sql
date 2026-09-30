-- FarmNex CORE schema — the record of how Atharv's own Supabase project
-- (`farmnex`, Mumbai, ref wezayjatfhyeswlzvubk) was built on 2026-09-30.
--
-- What it is: the exact SQL that the backend's start-up `Base.metadata.create_all`
-- would run on an EMPTY database (generated from the models with SQLAlchemy's
-- create_mock_engine, not hand-written), plus "lock" lines that switch on
-- row-level security (RLS) for every core table.
--
-- Why RLS: the Flutter app never talks to Supabase directly. With RLS on and no
-- policies, Supabase's public API can't read these tables, while the backend
-- (which connects as the database owner `postgres`, which bypasses RLS) works
-- exactly as before.
--
-- When to run it: ONLY on a brand-new, empty database (for example a fresh
-- test project). It is NOT safe to run twice (plain CREATE TABLE) — the second
-- run just stops with "already exists" and changes nothing. On the main DB it
-- has already been applied; do not run it there again.
--
-- Order for a fresh DB: 001 → 010 → 011 → 012 → later component files.
-- If a model in app/models changes, regenerate this file (see migrations/README.md).

BEGIN;

CREATE TYPE auth_event_type AS ENUM ('LOGIN_SUCCESS', 'LOGIN_FAILED', 'OTP_REQUESTED', 'OTP_VERIFIED', 'OTP_FAILED', 'LOGOUT', 'ACCOUNT_LOCKED', 'ACCOUNT_UNLOCKED', 'PHONE_CHANGED', 'PIN_CHANGED');

CREATE TYPE otp_purpose AS ENUM ('REGISTER', 'LOGIN', 'CHANGE_PHONE', 'RESET_PIN');

CREATE TYPE account_status AS ENUM ('ACTIVE', 'SUSPENDED', 'LOCKED', 'DISABLED');

CREATE TABLE otp_verifications (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	phone_number VARCHAR(20) NOT NULL, 
	purpose otp_purpose NOT NULL, 
	provider_name VARCHAR(50) NOT NULL, 
	provider_request_id VARCHAR(100) NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	verified_at TIMESTAMP WITH TIME ZONE, 
	attempt_count INTEGER DEFAULT '0' NOT NULL, 
	max_attempts INTEGER DEFAULT '5' NOT NULL, 
	resend_count INTEGER DEFAULT '0' NOT NULL, 
	last_sent_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_otp_verifications_phone_number ON otp_verifications (phone_number);

CREATE INDEX ix_otp_verifications_expires_at ON otp_verifications (expires_at);

CREATE INDEX ix_otp_verifications_purpose ON otp_verifications (purpose);

CREATE UNIQUE INDEX ix_otp_verifications_public_id ON otp_verifications (public_id);

CREATE INDEX ix_otp_verifications_provider_request_id ON otp_verifications (provider_request_id);

CREATE TABLE roles (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	description TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_roles_public_id ON roles (public_id);

CREATE UNIQUE INDEX ix_roles_name ON roles (name);

CREATE TABLE crop_types (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	name VARCHAR(150) NOT NULL, 
	scientific_name VARCHAR(200), 
	description TEXT, 
	category VARCHAR(100), 
	default_unit VARCHAR(30) NOT NULL, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE INDEX ix_crop_types_category ON crop_types (category);

CREATE INDEX ix_crop_types_created_at ON crop_types (created_at);

CREATE UNIQUE INDEX ix_crop_types_public_id ON crop_types (public_id);

CREATE TABLE bid_events (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	listing_id INTEGER NOT NULL, 
	created_by_id INTEGER NOT NULL, 
	starts_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	ends_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	starting_price NUMERIC(14, 2) NOT NULL, 
	minimum_increment NUMERIC(14, 2) NOT NULL, 
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	winner_bid_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_bid_events_status ON bid_events (status);

CREATE INDEX ix_bid_events_created_by_id ON bid_events (created_by_id);

CREATE INDEX ix_bid_events_starts_at ON bid_events (starts_at);

CREATE UNIQUE INDEX ix_bid_events_public_id ON bid_events (public_id);

CREATE INDEX ix_bid_events_winner_bid_id ON bid_events (winner_bid_id);

CREATE INDEX ix_bid_events_created_at ON bid_events (created_at);

CREATE INDEX ix_bid_events_listing_id ON bid_events (listing_id);

CREATE INDEX ix_bid_events_ends_at ON bid_events (ends_at);

CREATE TABLE bids (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	bid_event_id INTEGER NOT NULL, 
	bidder_id INTEGER NOT NULL, 
	amount NUMERIC(14, 2) NOT NULL, 
	quantity NUMERIC(14, 3), 
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	placed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_bids_bid_event_id ON bids (bid_event_id);

CREATE INDEX ix_bids_created_at ON bids (created_at);

CREATE INDEX ix_bids_status ON bids (status);

CREATE INDEX ix_bids_placed_at ON bids (placed_at);

CREATE UNIQUE INDEX ix_bids_public_id ON bids (public_id);

CREATE INDEX ix_bids_bidder_id ON bids (bidder_id);

CREATE TABLE users (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	phone_number VARCHAR(20) NOT NULL, 
	phone_verified_at TIMESTAMP WITH TIME ZONE, 
	pin_hash VARCHAR(255), 
	role_id INTEGER NOT NULL, 
	account_status account_status NOT NULL, 
	last_login_at TIMESTAMP WITH TIME ZONE, 
	first_name VARCHAR(100), 
	middle_name VARCHAR(100), 
	surname VARCHAR(100), 
	alternate_phone_number VARCHAR(20), 
	alternate_phone_verified_at TIMESTAMP WITH TIME ZONE, 
	date_of_birth DATE, 
	gender VARCHAR(30), 
	profile_image_path VARCHAR(1024), 
	preferred_language VARCHAR(20), 
	timezone VARCHAR(50), 
	occupation VARCHAR(150), 
	bio TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(role_id) REFERENCES roles (id), 
	UNIQUE (alternate_phone_number)
);

CREATE UNIQUE INDEX ix_users_public_id ON users (public_id);

CREATE INDEX ix_users_role_id ON users (role_id);

CREATE UNIQUE INDEX ix_users_phone_number ON users (phone_number);

CREATE TABLE auth_events (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	user_id INTEGER, 
	phone_number VARCHAR(20), 
	event_type auth_event_type NOT NULL, 
	ip_address INET, 
	user_agent TEXT, 
	failure_reason VARCHAR(255), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_auth_events_user_id ON auth_events (user_id);

CREATE INDEX ix_auth_events_event_type ON auth_events (event_type);

CREATE INDEX ix_auth_events_phone_number ON auth_events (phone_number);

CREATE INDEX ix_auth_events_created_at ON auth_events (created_at);

CREATE UNIQUE INDEX ix_auth_events_public_id ON auth_events (public_id);

CREATE TABLE farms (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	user_id INTEGER NOT NULL, 
	farm_name VARCHAR(150) NOT NULL, 
	description TEXT, 
	address_line_1 VARCHAR(255) NOT NULL, 
	address_line_2 VARCHAR(255), 
	landmark VARCHAR(255), 
	village VARCHAR(150), 
	city VARCHAR(150), 
	district VARCHAR(150), 
	state VARCHAR(150) NOT NULL, 
	postal_code VARCHAR(20) NOT NULL, 
	country VARCHAR(100) NOT NULL, 
	latitude NUMERIC(10, 7), 
	longitude NUMERIC(10, 7), 
	farm_file_path VARCHAR(1024), 
	farm_file_content_type VARCHAR(100), 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_farms_user_id ON farms (user_id);

CREATE UNIQUE INDEX ix_farms_public_id ON farms (public_id);

CREATE TABLE user_sessions (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	user_id INTEGER NOT NULL, 
	token_family UUID NOT NULL, 
	refresh_token_hash VARCHAR(255) NOT NULL, 
	ip_address INET, 
	user_agent TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	revoked_at TIMESTAMP WITH TIME ZONE, 
	last_used_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	UNIQUE (refresh_token_hash)
);

CREATE UNIQUE INDEX ix_user_sessions_public_id ON user_sessions (public_id);

CREATE INDEX ix_user_sessions_token_family ON user_sessions (token_family);

CREATE INDEX ix_user_sessions_revoked_at ON user_sessions (revoked_at);

CREATE INDEX ix_user_sessions_user_id ON user_sessions (user_id);

CREATE INDEX ix_user_sessions_expires_at ON user_sessions (expires_at);

CREATE TABLE audit_logs (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	actor_id INTEGER, 
	action VARCHAR(100) NOT NULL, 
	entity_type VARCHAR(100) NOT NULL, 
	entity_id INTEGER, 
	request_id VARCHAR(100), 
	ip_address VARCHAR(64), 
	user_agent TEXT, 
	before_data JSONB, 
	after_data JSONB, 
	created_at_override TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_audit_logs_action ON audit_logs (action);

CREATE INDEX ix_audit_logs_entity_type ON audit_logs (entity_type);

CREATE UNIQUE INDEX ix_audit_logs_public_id ON audit_logs (public_id);

CREATE INDEX ix_audit_logs_request_id ON audit_logs (request_id);

CREATE INDEX ix_audit_logs_created_at ON audit_logs (created_at);

CREATE INDEX ix_audit_logs_actor_id ON audit_logs (actor_id);

CREATE INDEX ix_audit_logs_entity_id ON audit_logs (entity_id);

CREATE TABLE buyer_demand_requests (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	buyer_id INTEGER NOT NULL, 
	crop_type_id INTEGER NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	description TEXT, 
	quantity NUMERIC(14, 3) NOT NULL, 
	unit VARCHAR(30) NOT NULL, 
	target_price NUMERIC(14, 2), 
	delivery_city VARCHAR(150), 
	delivery_state VARCHAR(150), 
	needed_by DATE, 
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(buyer_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(crop_type_id) REFERENCES crop_types (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_buyer_demand_requests_public_id ON buyer_demand_requests (public_id);

CREATE INDEX ix_buyer_demand_requests_buyer_id ON buyer_demand_requests (buyer_id);

CREATE INDEX ix_buyer_demand_requests_created_at ON buyer_demand_requests (created_at);

CREATE INDEX ix_buyer_demand_requests_crop_type_id ON buyer_demand_requests (crop_type_id);

CREATE INDEX ix_buyer_demand_requests_status ON buyer_demand_requests (status);

CREATE INDEX ix_buyer_demand_requests_needed_by ON buyer_demand_requests (needed_by);

CREATE TABLE orders (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	buyer_id INTEGER NOT NULL, 
	order_number VARCHAR(50) NOT NULL, 
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	currency VARCHAR(10) DEFAULT 'INR' NOT NULL, 
	subtotal NUMERIC(14, 2) NOT NULL, 
	delivery_fee NUMERIC(14, 2) DEFAULT '0' NOT NULL, 
	tax_amount NUMERIC(14, 2) DEFAULT '0' NOT NULL, 
	discount_amount NUMERIC(14, 2) DEFAULT '0' NOT NULL, 
	total_amount NUMERIC(14, 2) NOT NULL, 
	delivery_address_snapshot JSONB, 
	placed_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(buyer_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_orders_public_id ON orders (public_id);

CREATE INDEX ix_orders_placed_at ON orders (placed_at);

CREATE INDEX ix_orders_created_at ON orders (created_at);

CREATE INDEX ix_orders_buyer_id ON orders (buyer_id);

CREATE INDEX ix_orders_status ON orders (status);

CREATE UNIQUE INDEX ix_orders_order_number ON orders (order_number);

CREATE TABLE notifications (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	user_id INTEGER NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	message TEXT NOT NULL, 
	notification_type VARCHAR(50) NOT NULL, 
	data JSONB, 
	is_read BOOLEAN DEFAULT 'true' NOT NULL, 
	read_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_notifications_public_id ON notifications (public_id);

CREATE INDEX ix_notifications_is_read ON notifications (is_read);

CREATE INDEX ix_notifications_read_at ON notifications (read_at);

CREATE INDEX ix_notifications_user_id ON notifications (user_id);

CREATE INDEX ix_notifications_created_at ON notifications (created_at);

CREATE INDEX ix_notifications_notification_type ON notifications (notification_type);

CREATE TABLE farm_crops (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	farmer_id INTEGER NOT NULL, 
	farm_id INTEGER NOT NULL, 
	crop_type_id INTEGER NOT NULL, 
	variety VARCHAR(150), 
	sowing_date DATE, 
	expected_harvest_date DATE, 
	area_value NUMERIC(14, 3), 
	area_unit VARCHAR(30), 
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	notes TEXT, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(farmer_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(farm_id) REFERENCES farms (id) ON DELETE CASCADE, 
	FOREIGN KEY(crop_type_id) REFERENCES crop_types (id) ON DELETE CASCADE
);

CREATE INDEX ix_farm_crops_crop_type_id ON farm_crops (crop_type_id);

CREATE UNIQUE INDEX ix_farm_crops_public_id ON farm_crops (public_id);

CREATE INDEX ix_farm_crops_farmer_id ON farm_crops (farmer_id);

CREATE INDEX ix_farm_crops_status ON farm_crops (status);

CREATE INDEX ix_farm_crops_created_at ON farm_crops (created_at);

CREATE INDEX ix_farm_crops_farm_id ON farm_crops (farm_id);

CREATE TABLE deliveries (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	order_id INTEGER NOT NULL, 
	seller_id INTEGER NOT NULL, 
	farm_id INTEGER NOT NULL, 
	delivery_agent_id INTEGER, 
	tracking_number VARCHAR(100), 
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	pickup_address_snapshot JSONB, 
	delivery_address_snapshot JSONB, 
	expected_at TIMESTAMP WITH TIME ZONE, 
	delivered_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(seller_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(farm_id) REFERENCES farms (id) ON DELETE CASCADE, 
	FOREIGN KEY(delivery_agent_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_deliveries_tracking_number ON deliveries (tracking_number);

CREATE INDEX ix_deliveries_created_at ON deliveries (created_at);

CREATE INDEX ix_deliveries_status ON deliveries (status);

CREATE INDEX ix_deliveries_seller_id ON deliveries (seller_id);

CREATE INDEX ix_deliveries_delivered_at ON deliveries (delivered_at);

CREATE INDEX ix_deliveries_farm_id ON deliveries (farm_id);

CREATE UNIQUE INDEX ix_deliveries_public_id ON deliveries (public_id);

CREATE INDEX ix_deliveries_delivery_agent_id ON deliveries (delivery_agent_id);

CREATE INDEX ix_deliveries_order_id ON deliveries (order_id);

CREATE INDEX ix_deliveries_expected_at ON deliveries (expected_at);

CREATE TABLE order_disputes (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	order_id INTEGER NOT NULL, 
	raised_by_id INTEGER NOT NULL, 
	against_user_id INTEGER, 
	reason VARCHAR(100) NOT NULL, 
	description TEXT NOT NULL, 
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	resolution TEXT, 
	resolved_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(raised_by_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(against_user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_order_disputes_public_id ON order_disputes (public_id);

CREATE INDEX ix_order_disputes_resolved_at ON order_disputes (resolved_at);

CREATE INDEX ix_order_disputes_against_user_id ON order_disputes (against_user_id);

CREATE INDEX ix_order_disputes_order_id ON order_disputes (order_id);

CREATE INDEX ix_order_disputes_raised_by_id ON order_disputes (raised_by_id);

CREATE INDEX ix_order_disputes_status ON order_disputes (status);

CREATE INDEX ix_order_disputes_reason ON order_disputes (reason);

CREATE INDEX ix_order_disputes_created_at ON order_disputes (created_at);

CREATE TABLE payments (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	order_id INTEGER NOT NULL, 
	payer_id INTEGER NOT NULL, 
	provider VARCHAR(50) NOT NULL, 
	provider_payment_id VARCHAR(150), 
	amount NUMERIC(14, 2) NOT NULL, 
	currency VARCHAR(10) DEFAULT 'INR' NOT NULL, 
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	payment_method VARCHAR(50), 
	paid_at TIMESTAMP WITH TIME ZONE, 
	failure_reason VARCHAR(255), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(payer_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_payments_status ON payments (status);

CREATE INDEX ix_payments_paid_at ON payments (paid_at);

CREATE INDEX ix_payments_payer_id ON payments (payer_id);

CREATE INDEX ix_payments_provider_payment_id ON payments (provider_payment_id);

CREATE UNIQUE INDEX ix_payments_public_id ON payments (public_id);

CREATE INDEX ix_payments_created_at ON payments (created_at);

CREATE INDEX ix_payments_order_id ON payments (order_id);

CREATE TABLE ai_predictions (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	user_id INTEGER, 
	farm_id INTEGER, 
	farm_crop_id INTEGER, 
	model_name VARCHAR(150) NOT NULL, 
	model_version VARCHAR(80), 
	prediction_type VARCHAR(80) NOT NULL, 
	prediction JSONB NOT NULL, 
	confidence NUMERIC(6, 5), 
	predicted_for TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(farm_id) REFERENCES farms (id) ON DELETE CASCADE, 
	FOREIGN KEY(farm_crop_id) REFERENCES farm_crops (id) ON DELETE CASCADE
);

CREATE INDEX ix_ai_predictions_predicted_for ON ai_predictions (predicted_for);

CREATE INDEX ix_ai_predictions_farm_id ON ai_predictions (farm_id);

CREATE INDEX ix_ai_predictions_farm_crop_id ON ai_predictions (farm_crop_id);

CREATE UNIQUE INDEX ix_ai_predictions_public_id ON ai_predictions (public_id);

CREATE INDEX ix_ai_predictions_user_id ON ai_predictions (user_id);

CREATE INDEX ix_ai_predictions_created_at ON ai_predictions (created_at);

CREATE INDEX ix_ai_predictions_prediction_type ON ai_predictions (prediction_type);

CREATE TABLE crop_batches (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	farm_crop_id INTEGER NOT NULL, 
	batch_code VARCHAR(80) NOT NULL, 
	harvest_date DATE, 
	quantity NUMERIC(14, 3) NOT NULL, 
	available_quantity NUMERIC(14, 3) NOT NULL, 
	unit VARCHAR(30) NOT NULL, 
	quality_grade VARCHAR(50), 
	organic_certified BOOLEAN DEFAULT 'true' NOT NULL, 
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(farm_crop_id) REFERENCES farm_crops (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_crop_batches_batch_code ON crop_batches (batch_code);

CREATE UNIQUE INDEX ix_crop_batches_public_id ON crop_batches (public_id);

CREATE INDEX ix_crop_batches_created_at ON crop_batches (created_at);

CREATE INDEX ix_crop_batches_farm_crop_id ON crop_batches (farm_crop_id);

CREATE INDEX ix_crop_batches_status ON crop_batches (status);

CREATE INDEX ix_crop_batches_harvest_date ON crop_batches (harvest_date);

CREATE TABLE delivery_proofs (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	delivery_id INTEGER NOT NULL, 
	uploaded_by_id INTEGER NOT NULL, 
	storage_path VARCHAR(1024) NOT NULL, 
	content_type VARCHAR(100) NOT NULL, 
	proof_type VARCHAR(50) NOT NULL, 
	captured_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(delivery_id) REFERENCES deliveries (id) ON DELETE CASCADE, 
	FOREIGN KEY(uploaded_by_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_delivery_proofs_uploaded_by_id ON delivery_proofs (uploaded_by_id);

CREATE INDEX ix_delivery_proofs_delivery_id ON delivery_proofs (delivery_id);

CREATE UNIQUE INDEX ix_delivery_proofs_public_id ON delivery_proofs (public_id);

CREATE INDEX ix_delivery_proofs_created_at ON delivery_proofs (created_at);

CREATE TABLE delivery_tracking_events (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	delivery_id INTEGER NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	latitude NUMERIC(10, 7), 
	longitude NUMERIC(10, 7), 
	location_text VARCHAR(255), 
	notes TEXT, 
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(delivery_id) REFERENCES deliveries (id) ON DELETE CASCADE
);

CREATE INDEX ix_delivery_tracking_events_created_at ON delivery_tracking_events (created_at);

CREATE INDEX ix_delivery_tracking_events_recorded_at ON delivery_tracking_events (recorded_at);

CREATE UNIQUE INDEX ix_delivery_tracking_events_public_id ON delivery_tracking_events (public_id);

CREATE INDEX ix_delivery_tracking_events_status ON delivery_tracking_events (status);

CREATE INDEX ix_delivery_tracking_events_delivery_id ON delivery_tracking_events (delivery_id);

CREATE TABLE farm_crop_activities (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	farm_crop_id INTEGER NOT NULL, 
	activity_type VARCHAR(50) NOT NULL, 
	activity_date TIMESTAMP WITH TIME ZONE NOT NULL, 
	description TEXT, 
	input_name VARCHAR(150), 
	input_quantity NUMERIC(14, 3), 
	input_unit VARCHAR(30), 
	cost NUMERIC(14, 2), 
	notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(farm_crop_id) REFERENCES farm_crops (id) ON DELETE CASCADE
);

CREATE INDEX ix_farm_crop_activities_farm_crop_id ON farm_crop_activities (farm_crop_id);

CREATE UNIQUE INDEX ix_farm_crop_activities_public_id ON farm_crop_activities (public_id);

CREATE INDEX ix_farm_crop_activities_activity_type ON farm_crop_activities (activity_type);

CREATE INDEX ix_farm_crop_activities_activity_date ON farm_crop_activities (activity_date);

CREATE INDEX ix_farm_crop_activities_created_at ON farm_crop_activities (created_at);

CREATE TABLE ai_recommendations (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	user_id INTEGER NOT NULL, 
	farm_id INTEGER, 
	farm_crop_id INTEGER, 
	prediction_id INTEGER, 
	recommendation_type VARCHAR(80) NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	description TEXT NOT NULL, 
	priority VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	metadata_json JSONB, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(farm_id) REFERENCES farms (id) ON DELETE CASCADE, 
	FOREIGN KEY(farm_crop_id) REFERENCES farm_crops (id) ON DELETE CASCADE, 
	FOREIGN KEY(prediction_id) REFERENCES ai_predictions (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_ai_recommendations_public_id ON ai_recommendations (public_id);

CREATE INDEX ix_ai_recommendations_user_id ON ai_recommendations (user_id);

CREATE INDEX ix_ai_recommendations_status ON ai_recommendations (status);

CREATE INDEX ix_ai_recommendations_created_at ON ai_recommendations (created_at);

CREATE INDEX ix_ai_recommendations_recommendation_type ON ai_recommendations (recommendation_type);

CREATE INDEX ix_ai_recommendations_priority ON ai_recommendations (priority);

CREATE INDEX ix_ai_recommendations_farm_id ON ai_recommendations (farm_id);

CREATE INDEX ix_ai_recommendations_farm_crop_id ON ai_recommendations (farm_crop_id);

CREATE INDEX ix_ai_recommendations_prediction_id ON ai_recommendations (prediction_id);

CREATE TABLE product_listings (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	seller_id INTEGER NOT NULL, 
	farm_id INTEGER NOT NULL, 
	crop_batch_id INTEGER NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	description TEXT, 
	listing_type VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	price NUMERIC(14, 2) NOT NULL, 
	currency VARCHAR(10) DEFAULT 'INR' NOT NULL, 
	quantity NUMERIC(14, 3) NOT NULL, 
	available_quantity NUMERIC(14, 3) NOT NULL, 
	unit VARCHAR(30) NOT NULL, 
	minimum_order_quantity NUMERIC(14, 3), 
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	starts_at TIMESTAMP WITH TIME ZONE, 
	ends_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(seller_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(farm_id) REFERENCES farms (id) ON DELETE CASCADE, 
	FOREIGN KEY(crop_batch_id) REFERENCES crop_batches (id) ON DELETE CASCADE
);

CREATE INDEX ix_product_listings_title ON product_listings (title);

CREATE INDEX ix_product_listings_crop_batch_id ON product_listings (crop_batch_id);

CREATE INDEX ix_product_listings_ends_at ON product_listings (ends_at);

CREATE UNIQUE INDEX ix_product_listings_public_id ON product_listings (public_id);

CREATE INDEX ix_product_listings_farm_id ON product_listings (farm_id);

CREATE INDEX ix_product_listings_listing_type ON product_listings (listing_type);

CREATE INDEX ix_product_listings_seller_id ON product_listings (seller_id);

CREATE INDEX ix_product_listings_status ON product_listings (status);

CREATE INDEX ix_product_listings_starts_at ON product_listings (starts_at);

CREATE INDEX ix_product_listings_created_at ON product_listings (created_at);

CREATE TABLE waste_records (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	farm_id INTEGER NOT NULL, 
	crop_batch_id INTEGER, 
	recorded_by_id INTEGER NOT NULL, 
	waste_type VARCHAR(80) NOT NULL, 
	quantity NUMERIC(14, 3) NOT NULL, 
	unit VARCHAR(30) NOT NULL, 
	reason TEXT, 
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(farm_id) REFERENCES farms (id) ON DELETE CASCADE, 
	FOREIGN KEY(crop_batch_id) REFERENCES crop_batches (id) ON DELETE CASCADE, 
	FOREIGN KEY(recorded_by_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_waste_records_farm_id ON waste_records (farm_id);

CREATE INDEX ix_waste_records_status ON waste_records (status);

CREATE INDEX ix_waste_records_recorded_at ON waste_records (recorded_at);

CREATE INDEX ix_waste_records_created_at ON waste_records (created_at);

CREATE INDEX ix_waste_records_waste_type ON waste_records (waste_type);

CREATE UNIQUE INDEX ix_waste_records_public_id ON waste_records (public_id);

CREATE INDEX ix_waste_records_crop_batch_id ON waste_records (crop_batch_id);

CREATE INDEX ix_waste_records_recorded_by_id ON waste_records (recorded_by_id);

CREATE TABLE order_items (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	order_id INTEGER NOT NULL, 
	seller_id INTEGER NOT NULL, 
	farm_id INTEGER NOT NULL, 
	listing_id INTEGER, 
	crop_batch_id INTEGER, 
	title_snapshot VARCHAR(200) NOT NULL, 
	unit_price NUMERIC(14, 2) NOT NULL, 
	quantity NUMERIC(14, 3) NOT NULL, 
	unit VARCHAR(30) NOT NULL, 
	line_total NUMERIC(14, 2) NOT NULL, 
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(seller_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(farm_id) REFERENCES farms (id) ON DELETE CASCADE, 
	FOREIGN KEY(listing_id) REFERENCES product_listings (id) ON DELETE CASCADE, 
	FOREIGN KEY(crop_batch_id) REFERENCES crop_batches (id) ON DELETE CASCADE
);

CREATE INDEX ix_order_items_order_id ON order_items (order_id);

CREATE INDEX ix_order_items_status ON order_items (status);

CREATE INDEX ix_order_items_created_at ON order_items (created_at);

CREATE INDEX ix_order_items_farm_id ON order_items (farm_id);

CREATE INDEX ix_order_items_listing_id ON order_items (listing_id);

CREATE INDEX ix_order_items_seller_id ON order_items (seller_id);

CREATE INDEX ix_order_items_crop_batch_id ON order_items (crop_batch_id);

CREATE UNIQUE INDEX ix_order_items_public_id ON order_items (public_id);

CREATE TABLE product_images (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	listing_id INTEGER NOT NULL, 
	storage_path VARCHAR(1024) NOT NULL, 
	content_type VARCHAR(100) NOT NULL, 
	sort_order INTEGER DEFAULT '0' NOT NULL, 
	is_primary BOOLEAN DEFAULT 'true' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(listing_id) REFERENCES product_listings (id) ON DELETE CASCADE
);

CREATE INDEX ix_product_images_listing_id ON product_images (listing_id);

CREATE UNIQUE INDEX ix_product_images_public_id ON product_images (public_id);

CREATE INDEX ix_product_images_created_at ON product_images (created_at);

CREATE TABLE reviews (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	reviewer_id INTEGER NOT NULL, 
	order_id INTEGER NOT NULL, 
	listing_id INTEGER, 
	reviewee_id INTEGER NOT NULL, 
	rating INTEGER NOT NULL, 
	title VARCHAR(200), 
	comment TEXT, 
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(reviewer_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(listing_id) REFERENCES product_listings (id) ON DELETE CASCADE, 
	FOREIGN KEY(reviewee_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_reviews_status ON reviews (status);

CREATE UNIQUE INDEX ix_reviews_public_id ON reviews (public_id);

CREATE INDEX ix_reviews_created_at ON reviews (created_at);

CREATE INDEX ix_reviews_order_id ON reviews (order_id);

CREATE INDEX ix_reviews_reviewee_id ON reviews (reviewee_id);

CREATE INDEX ix_reviews_listing_id ON reviews (listing_id);

CREATE INDEX ix_reviews_reviewer_id ON reviews (reviewer_id);

CREATE TABLE waste_utilization_listings (
	id SERIAL NOT NULL, 
	public_id UUID NOT NULL, 
	waste_record_id INTEGER NOT NULL, 
	seller_id INTEGER NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	description TEXT, 
	utilization_type VARCHAR(50) NOT NULL, 
	quantity NUMERIC(14, 3) NOT NULL, 
	unit VARCHAR(30) NOT NULL, 
	price NUMERIC(14, 2) NOT NULL, 
	status VARCHAR(30) DEFAULT 'ACTIVE' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(waste_record_id) REFERENCES waste_records (id) ON DELETE CASCADE, 
	FOREIGN KEY(seller_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_waste_utilization_listings_waste_record_id ON waste_utilization_listings (waste_record_id);

CREATE INDEX ix_waste_utilization_listings_seller_id ON waste_utilization_listings (seller_id);

CREATE INDEX ix_waste_utilization_listings_created_at ON waste_utilization_listings (created_at);

CREATE INDEX ix_waste_utilization_listings_status ON waste_utilization_listings (status);

CREATE INDEX ix_waste_utilization_listings_utilization_type ON waste_utilization_listings (utilization_type);

CREATE UNIQUE INDEX ix_waste_utilization_listings_public_id ON waste_utilization_listings (public_id);

ALTER TABLE bid_events ADD FOREIGN KEY(winner_bid_id) REFERENCES bids (id) ON DELETE CASCADE;

ALTER TABLE bids ADD FOREIGN KEY(bid_event_id) REFERENCES bid_events (id) ON DELETE CASCADE;

ALTER TABLE bid_events ADD FOREIGN KEY(created_by_id) REFERENCES users (id) ON DELETE CASCADE;

ALTER TABLE bids ADD FOREIGN KEY(bidder_id) REFERENCES users (id) ON DELETE CASCADE;

ALTER TABLE bid_events ADD FOREIGN KEY(listing_id) REFERENCES product_listings (id) ON DELETE CASCADE;

ALTER TABLE public.otp_verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crop_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bid_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bids ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auth_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.farms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.buyer_demand_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.farm_crops ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_disputes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crop_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.delivery_proofs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.delivery_tracking_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.farm_crop_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.waste_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.waste_utilization_listings ENABLE ROW LEVEL SECURITY;

COMMIT;
