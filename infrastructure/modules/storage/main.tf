resource "aws_s3_bucket" "content" {
  bucket = "exeaws26-content-${var.env_name}"
  tags = { Name = "exeaws26-content-${var.env_name}" }
}

resource "aws_s3_bucket_public_access_block" "content" {
  bucket = aws_s3_bucket.content.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_iam_policy" "s3_content" {
  name        = "${var.env_name}-s3-content-policy"
  description = "Allow ECS task role to read and write content objects"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["s3:GetObject", "s3:PutObject"]
      Resource = "${aws_s3_bucket.content.arn}/*"
    }]
  })
}
