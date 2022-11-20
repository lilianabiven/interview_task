# Summary
I wrote a python script which checks for expensive EC2 and RDS instances, and sends a report via the Simple Notification Service.

# Requirements
Cost explorer needs to be activated first via the management console, before using the API. To do this, just go the Cost Explorer page for the first time, as instructed here: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-enable.html
After activation, you have to wait 24 hours before getting any data.

You should have an AWS config in `~/.aws/config`, with the following content:
```
[<profile_name>]
aws_access_key_id = <id>
aws_secret_access_key = <secret_key>
region = <region>
```

You can have multiple accounts in your config.

This was only tested with python 3.10, but I suppose it works with any version >=3.8

You need to install the AWS `boto3` module. 

The Simple Notification Service is set up using email notifications.
Deploy using `cloud_formation.template`. Remember to fill in the parameter `email_address` beforehand. This is the email
address the inspection report will be sent to.

# Usage


`python3 cost_checker.py <profile_name> <amount_threshold> <sns_topic_arn> <csv_report_filename>`

- `amount_threshold` is the daily amount defining an expensive instance. If an instance has exceeded this amount 
in the past 24 hours, it will be included in the inspection report.   
- `sns_topic_arn` is the ARN of the SNS topic used to send the inspection report.
- `csv_report_filename` is the name of a file that will be filled every time a report is sent, to keep a history 
of the inspection reports. 

To make this tool run once per weekday at 8:00, add the following cron to your machine:

`0 8 * * 1-5 python3 cost_checker.py <profile_name> <amount_threshold> <sns_topic_arn> <csv_report_filename>`

# Examples
To check for instances which cost over 100 USD per day:

`python3 cost_checker.py costChecker1 100 arn:aws:sns:eu-central-1:752594615588:CostReports csv_report.csv`

## Example csv report

| instance_type | amount | currency | start_date | end_date   |
|---------------|--------|----------|------------|------------|
| db.t2_micro   | 120.7  | USD      | 2022-11-17 | 2022-11-18 |
| t2.micro      | 189.9  | USD      | 2022-11-18 | 2022-11-19 |
| db.t2_micro   | 111.3  | USD      | 2022-11-18 | 2022-11-19 |

## Example email content
```
In the last 24 hours:
A t2.micro instance cost 189.9 USD
A db.t2_micro instance cost 111.3 USD
```

# Improvements: 
- The report only includes the instance types. To get the instance ids, I think you'd need to enable 
**Hourly and Resource Level Data** in the Cost explorer settings, and the use the method 
`get_cost_and_usage_with_resources` instead of `get_cost_and_usage_with_resources`.
- Error handling is minimal and could definitely be improved
