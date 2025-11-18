-- seed_bicycle_system.sql — Seed data for Bicycle Hire Purchase System
-- Run with: psql "$DATABASE_URL" -f database/seed_bicycle_system.sql

-- ======================================================================
-- CREATE BRANCHES (OFFICES) WITH BICYCLE SUPPORT
-- ======================================================================

INSERT INTO offices (id, name, allows_bicycle_sales, bicycle_display_order, operating_hours, public_description, map_coordinates) VALUES
('BR001', 'Jakarta Central Branch', TRUE, 1, 'Mon-Fri: 8:00-17:00, Sat: 9:00-15:00', 'Our flagship branch in the heart of Jakarta offering the widest selection of bicycles and financing options.', '{"lat": -6.200000, "lng": 106.816666}'),
('BR002', 'Surabaya Main Branch', TRUE, 2, 'Mon-Fri: 8:00-17:00, Sat: 9:00-14:00', 'Serving East Java with quality bicycles and flexible hire purchase plans.', '{"lat": -7.250445, "lng": 112.768845}'),
('BR003', 'Bandung West Branch', TRUE, 3, 'Mon-Fri: 8:30-17:00, Sat: 9:00-13:00', 'Your trusted partner for bicycle financing in West Java.', '{"lat": -6.914744, "lng": 107.609810}'),
('BR004', 'Medan North Branch', TRUE, 4, 'Mon-Fri: 8:00-17:00, Sat: 9:00-14:00', 'Bringing affordable bicycle financing to North Sumatra.', '{"lat": 3.597031, "lng": 98.678513}'),
('BR005', 'Semarang Central Java', TRUE, 5, 'Mon-Fri: 8:00-17:00, Sat: 9:00-13:00', 'Quality bicycles with easy payment terms for Central Java residents.', '{"lat": -6.966667, "lng": 110.416664}'),
('BR006', 'Makassar South Branch', TRUE, 6, 'Mon-Fri: 8:00-17:00', 'Eastern Indonesia''s premier bicycle hire purchase center.', '{"lat": -5.135399, "lng": 119.423790}'),
('BR007', 'Denpasar Bali Branch', TRUE, 7, 'Mon-Sat: 8:00-17:00', 'Island paradise with island pricing - affordable bicycle financing.', '{"lat": -8.670458, "lng": 115.212629}'),
('BR008', 'Palembang Branch', TRUE, 8, 'Mon-Fri: 8:00-17:00, Sat: 9:00-14:00', 'Serving South Sumatra with competitive bicycle financing.', '{"lat": -2.976074, "lng": 104.775460}'),
('BR009', 'Yogyakarta Branch', TRUE, 9, 'Mon-Fri: 8:00-17:00, Sat: 9:00-15:00', 'Cultural capital meets modern financing solutions.', '{"lat": -7.797068, "lng": 110.370529}'),
('BR010', 'Malang Branch', TRUE, 10, 'Mon-Fri: 8:30-17:00, Sat: 9:00-13:00', 'Your neighborhood bicycle financing specialist.', '{"lat": -7.966620, "lng": 112.632632}')
ON CONFLICT (id) DO UPDATE SET
  allows_bicycle_sales = EXCLUDED.allows_bicycle_sales,
  bicycle_display_order = EXCLUDED.bicycle_display_order,
  operating_hours = EXCLUDED.operating_hours,
  public_description = EXCLUDED.public_description,
  map_coordinates = EXCLUDED.map_coordinates;

-- ======================================================================
-- CREATE USERS WITH DIFFERENT ROLES
-- Note: Password for all users is "password123" (hashed with SHA256)
-- In production, use bcrypt or better hashing
-- ======================================================================

-- Admin user
INSERT INTO users (id, username, password_hash, roles_csv, metadata) VALUES
(gen_random_uuid(), 'admin', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'admin', '{}')
ON CONFLICT (username) DO NOTHING;

-- Branch Managers (one per branch)
INSERT INTO users (id, username, password_hash, roles_csv, metadata) VALUES
(gen_random_uuid(), 'manager.jakarta', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'branch_manager', '{"branch_id": "BR001"}'),
(gen_random_uuid(), 'manager.surabaya', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'branch_manager', '{"branch_id": "BR002"}'),
(gen_random_uuid(), 'manager.bandung', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'branch_manager', '{"branch_id": "BR003"}'),
(gen_random_uuid(), 'manager.medan', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'branch_manager', '{"branch_id": "BR004"}'),
(gen_random_uuid(), 'manager.semarang', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'branch_manager', '{"branch_id": "BR005"}')
ON CONFLICT (username) DO NOTHING;

-- Sales Agents
INSERT INTO users (id, username, password_hash, roles_csv, metadata) VALUES
(gen_random_uuid(), 'sales.agent1', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'sales_agent', '{}'),
(gen_random_uuid(), 'sales.agent2', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'sales_agent', '{}')
ON CONFLICT (username) DO NOTHING;

-- Inventory Managers
INSERT INTO users (id, username, password_hash, roles_csv, metadata) VALUES
(gen_random_uuid(), 'inventory.manager1', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'inventory_manager', '{}'),
(gen_random_uuid(), 'inventory.manager2', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'inventory_manager', '{}')
ON CONFLICT (username) DO NOTHING;

-- Finance Officers
INSERT INTO users (id, username, password_hash, roles_csv, metadata) VALUES
(gen_random_uuid(), 'finance.officer1', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'finance_officer', '{}'),
(gen_random_uuid(), 'finance.officer2', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'finance_officer', '{}')
ON CONFLICT (username) DO NOTHING;

-- Customer Service Representatives
INSERT INTO users (id, username, password_hash, roles_csv, metadata) VALUES
(gen_random_uuid(), 'customer.service1', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'customer_service', '{}'),
(gen_random_uuid(), 'customer.service2', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'customer_service', '{}')
ON CONFLICT (username) DO NOTHING;

-- Auditor
INSERT INTO users (id, username, password_hash, roles_csv, metadata) VALUES
(gen_random_uuid(), 'auditor', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'auditor', '{}')
ON CONFLICT (username) DO NOTHING;

-- ======================================================================
-- CREATE SAMPLE BICYCLES
-- ======================================================================

INSERT INTO bicycles (id, title, brand, model, year, condition, license_plate, frame_number, engine_number, purchase_price, cash_price, hire_purchase_price, duty_amount, registration_fee, mileage_km, description, branch_id, status, image_urls, thumbnail_url) VALUES
-- New Bicycles
('BK001', 'Honda Supra X 125 FI - New', 'Honda', 'Supra X 125 FI', 2024, 'NEW', 'B-1234-ABC', 'MH1JBK110FK100001', 'JBK1E1100001', 16500000, 17000000, 18500000, 500000, 200000, NULL, 'Brand new Honda Supra X 125 FI with fuel injection technology. Economical and reliable for daily commuting.', 'BR001', 'AVAILABLE', '["https://example.com/bikes/honda-supra-x-1.jpg", "https://example.com/bikes/honda-supra-x-2.jpg"]', 'https://example.com/bikes/honda-supra-x-thumb.jpg'),
('BK002', 'Yamaha NMAX 155 - New', 'Yamaha', 'NMAX 155', 2024, 'NEW', 'B-2345-DEF', 'MH3SG07106K000123', 'G315E0012345', 28000000, 29000000, 32000000, 800000, 250000, NULL, 'Latest Yamaha NMAX 155 with VVA technology. Premium scooter with sporty design and comfort.', 'BR001', 'AVAILABLE', '["https://example.com/bikes/yamaha-nmax-1.jpg"]', 'https://example.com/bikes/yamaha-nmax-thumb.jpg'),
('BK003', 'Bajaj Pulsar NS160 - New', 'Bajaj', 'Pulsar NS160', 2024, 'NEW', 'B-3456-GHI', 'MD2A21DH0LPJ12345', 'DTS160FI123456', 25000000, 26000000, 28500000, 600000, 200000, NULL, 'Powerful Bajaj Pulsar NS160 with sporty naked bike design. Perfect for enthusiasts.', 'BR002', 'AVAILABLE', '[]', NULL),
('BK004', 'TVS Apache RTR 160 4V - New', 'TVS', 'Apache RTR 160 4V', 2024, 'NEW', 'B-4567-JKL', 'MD632CD23KFN56789', 'RTR160-456789', 24000000, 25000000, 27500000, 550000, 200000, NULL, 'TVS Apache RTR 160 4V with race-tuned fuel injection. Built for performance.', 'BR002', 'AVAILABLE', '[]', NULL),
('BK005', 'Honda Vario 160 - New', 'Honda', 'Vario 160', 2024, 'NEW', 'B-5678-MNO', 'MH1JFK110FK200001', 'JFK1E1200001', 23500000, 24500000, 27000000, 500000, 200000, NULL, 'Honda Vario 160 - The ultimate stylish and practical scooter for urban mobility.', 'BR003', 'AVAILABLE', '[]', NULL),
('BK006', 'Yamaha Aerox 155 - New', 'Yamaha', 'Aerox 155', 2024, 'NEW', 'B-6789-PQR', 'MH3SG08106K000456', 'G315E0045678', 27000000, 28000000, 31000000, 700000, 250000, NULL, 'Yamaha Aerox 155 with aggressive styling and advanced features. Perfect for the young generation.', 'BR003', 'AVAILABLE', '[]', NULL),
('BK007', 'Honda BeAT Street - New', 'Honda', 'BeAT Street', 2024, 'NEW', 'B-7890-STU', 'MH1JFM110FK300001', 'JFM1E1300001', 16000000, 16500000, 18000000, 400000, 200000, NULL, 'Honda BeAT Street - Stylish, efficient, and affordable scooter for everyday use.', 'BR004', 'AVAILABLE', '[]', NULL),
('BK008', 'Yamaha Mio M3 125 - New', 'Yamaha', 'Mio M3 125', 2024, 'NEW', 'B-8901-VWX', 'MH3SG09106K000789', 'G125E0078901', 15500000, 16000000, 17500000, 350000, 200000, NULL, 'Yamaha Mio M3 125 - Fun, economical, and easy to ride for beginners.', 'BR004', 'AVAILABLE', '[]', NULL),
('BK009', 'Honda ADV 160 - New', 'Honda', 'ADV 160', 2024, 'NEW', 'B-9012-YZA', 'MH1JFN110FK400001', 'JFN1E1400001', 35000000, 36500000, 40000000, 1000000, 300000, NULL, 'Honda ADV 160 - Adventure scooter with premium features and long-distance comfort.', 'BR005', 'AVAILABLE', '[]', NULL),
('BK010', 'Yamaha Lexi 125 - New', 'Yamaha', 'Lexi 125', 2024, 'NEW', 'B-0123-BCD', 'MH3SG10106K000012', 'G125E0001234', 18500000, 19000000, 21000000, 450000, 200000, NULL, 'Yamaha Lexi 125 - Sporty automatic scooter with LED lighting and stylish design.', 'BR005', 'AVAILABLE', '[]', NULL),

-- Used Bicycles
('BK011', 'Honda Vario 125 - Used 2022', 'Honda', 'Vario 125', 2022, 'USED', 'B-1111-EFG', 'MH1JFP110FK500001', 'JFP1E1500001', 15000000, 16000000, 18000000, 0, 0, 15000, 'Well-maintained Honda Vario 125 from 2022. Perfect condition with regular service history.', 'BR006', 'AVAILABLE', '[]', NULL),
('BK012', 'Yamaha NMAX 155 - Used 2021', 'Yamaha', 'NMAX 155', 2021, 'USED', 'B-2222-HIJ', 'MH3SG11106K000345', 'G315E0034567', 22000000, 23000000, 26000000, 0, 0, 18000, 'Yamaha NMAX 155 from 2021 in excellent condition. Single owner with complete documents.', 'BR006', 'AVAILABLE', '[]', NULL),
('BK013', 'Honda Supra X 125 - Used 2020', 'Honda', 'Supra X 125', 2020, 'USED', 'B-3333-KLM', 'MH1JBK110FK600001', 'JBK1E1600001', 11000000, 12000000, 13500000, 0, 0, 25000, 'Reliable Honda Supra X 125 from 2020. Great fuel economy and low maintenance.', 'BR007', 'AVAILABLE', '[]', NULL),
('BK014', 'Yamaha Mio M3 - Used 2021', 'Yamaha', 'Mio M3', 2021, 'USED', 'B-4444-NOP', 'MH3SG12106K000678', 'G125E0067890', 12000000, 12500000, 14000000, 0, 0, 12000, 'Yamaha Mio M3 from 2021. Well cared for with minimal mileage.', 'BR007', 'AVAILABLE', '[]', NULL),
('BK015', 'Honda BeAT - Used 2019', 'Honda', 'BeAT', 2019, 'USED', 'B-5555-QRS', 'MH1JFM110FK700001', 'JFM1E1700001', 9500000, 10000000, 11500000, 0, 0, 30000, 'Honda BeAT from 2019. Economical scooter in good running condition.', 'BR008', 'AVAILABLE', '[]', NULL),
('BK016', 'Bajaj Pulsar 150 - Used 2020', 'Bajaj', 'Pulsar 150', 2020, 'USED', 'B-6666-TUV', 'MD2A22DH0LPJ67890', 'DTS150FI678901', 16000000, 17000000, 19000000, 0, 0, 22000, 'Bajaj Pulsar 150 from 2020. Powerful and reliable with sporty design.', 'BR008', 'AVAILABLE', '[]', NULL),
('BK017', 'TVS Apache RTR 160 - Used 2021', 'TVS', 'Apache RTR 160', 2021, 'USED', 'B-7777-WXY', 'MD632CD23KFN12345', 'RTR160-123456', 17000000, 18000000, 20000000, 0, 0, 16000, 'TVS Apache RTR 160 from 2021. Performance-oriented bike in excellent shape.', 'BR009', 'AVAILABLE', '[]', NULL),
('BK018', 'Honda Vario 150 - Used 2022', 'Honda', 'Vario 150', 2022, 'USED', 'B-8888-ZAB', 'MH1JFQ110FK800001', 'JFQ1E1800001', 19000000, 20000000, 22500000, 0, 0, 10000, 'Honda Vario 150 from 2022. Like new condition with low mileage.', 'BR009', 'AVAILABLE', '[]', NULL),
('BK019', 'Yamaha Aerox 155 - Used 2021', 'Yamaha', 'Aerox 155', 2021, 'USED', 'B-9999-CDE', 'MH3SG13106K000901', 'G315E0090123', 21000000, 22000000, 25000000, 0, 0, 14000, 'Yamaha Aerox 155 from 2021. Sporty scooter with premium features.', 'BR010', 'AVAILABLE', '[]', NULL),
('BK020', 'Honda ADV 150 - Used 2020', 'Honda', 'ADV 150', 2020, 'USED', 'B-0000-FGH', 'MH1JFR110FK900001', 'JFR1E1900001', 27000000, 28000000, 31000000, 0, 0, 20000, 'Honda ADV 150 from 2020. Adventure scooter perfect for long trips.', 'BR010', 'AVAILABLE', '[]', NULL);

-- ======================================================================
-- SUMMARY
-- ======================================================================
-- 10 branches created
-- 15+ users created with different roles
-- 20 bicycles created (10 new, 10 used)
-- All bicycles are in AVAILABLE status
-- Bicycles distributed across all branches
