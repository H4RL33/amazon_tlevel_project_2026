resource "aws_db_subnet_group" "main" {
  name       = "${var.env_name}-db-subnet-group"
  subnet_ids = var.private_subnet_ids
  tags       = { Name = "${var.env_name}-db-subnet-group" }
}

resource "aws_db_instance" "main" {
  identifier                = "${var.env_name}-postgres"
  engine                    = "postgres"
  engine_version            = "17"
  instance_class            = "db.t3.micro"
  allocated_storage         = 20
  storage_type              = "gp2"
  storage_encrypted         = true
  backup_retention_period   = 1
  backup_window             = "03:00-04:00"
  maintenance_window        = "sun:04:00-sun:05:00"
  db_name                   = "exeaws26"
  username                  = "exeaws26"
  password                  = var.db_password
  db_subnet_group_name      = aws_db_subnet_group.main.name
  vpc_security_group_ids    = [var.sg_rds_id]
  multi_az                  = false
  publicly_accessible       = false
  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.env_name}-postgres-final-snapshot"

  tags = { Name = "${var.env_name}-postgres" }
}
