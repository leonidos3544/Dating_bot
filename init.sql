CREATE TABLE IF NOT EXISTS profiles (
    id SERIAL PRIMARY KEY,
    tg_user_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Тестовая анкета (ID 999999, чтобы не конфликтовать с реальными пользователями)
INSERT INTO profiles (tg_user_id, name, age, bio) VALUES 
(999999, 'Тестовый Пользователь', 22, 'Люблю кофе и Python');
