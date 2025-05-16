PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -c "INSERT INTO subjects (name, age) VALUES \
('Kate', 40), \
('Elizabeth', 35), \
('Alice', 50), \
('Sophia', 32), \
('Emma', 25), \
('Olivia', 30), \
('Charlotte', 28), \
('Amelia', 45), \
('Mia', 55), \
('Isabella', 60);"
