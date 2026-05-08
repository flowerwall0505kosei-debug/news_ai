USE news_ai;
CREATE TABLE news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    summary TEXT,
    importance INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
select *
from news;
DESCRIBE news;
INSERT INTO news (title, url, summary, importance)
VALUES (
        'OpenAIが新モデル発表',
        'https://example.com',
        'AIの性能が大幅に向上した',
        5
    );
ALTER TABLE news
MODIFY url VARCHAR(500);
ALTER TABLE news
ADD UNIQUE (url);
ALTER TABLE news
ADD COLUMN category VARCHAR(50);
ALTER TABLE news
ADD COLUMN reason TEXT;
ALTER TABLE news
ADD COLUMN published_at DATETIME;
DELETE FROM news;
SELECT *
FROM news;
TRUNCATE TABLE news;