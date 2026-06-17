output "bucket_name" {
  value = aws_s3_bucket.content.bucket
}

output "bucket_arn" {
  value = aws_s3_bucket.content.arn
}

output "s3_policy_arn" {
  value = aws_iam_policy.s3_content.arn
}
