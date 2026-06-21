INSERT INTO storage.dim_review_score(review_score, score_label)
VALUES
    (1, 'very bad'),
    (2, 'bad'),
    (3, 'neutral'),
    (4, 'good'),
    (5, 'very good')
ON CONFLICT (review_score) DO UPDATE
SET score_label = EXCLUDED.score_label;
