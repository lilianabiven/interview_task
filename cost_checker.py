import boto3
import logging
from datetime import date, timedelta
import sys
import csv
import os


def get_costs(start_date, end_date, instance_type):
    # I didn't implement the NextPageToken parameter, as I only have a few instances,
    # but it would be needed for bigger infrastructures
    logging.info("Checking costs")
    client = boto3.client('ce')  # Cost explorer client
    return client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='DAILY',
        Filter={
            'Dimensions': {
                'Key': 'SERVICE',
                'Values': instance_type,
                'MatchOptions': [
                    'EQUALS'
                ]
            }
        },
        Metrics=[
            'UNBLENDED_COST',
        ],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'INSTANCE_TYPE'
            }
        ],
    )


def write_to_csv(instance_type, amount, currency, start_date, end_date, filename):
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        if not file_exists:
            headers = ['instance_type', 'amount', 'currency', 'start_date', 'end_date']
            csv_writer.writerow(headers)
        csv_writer.writerow([instance_type, amount, currency, start_date, end_date])


def generate_and_send_report(results, amount_threshold, topic_arn, csv_report_filename):
    logging.info('Generating report')
    message = ''
    for item in results['ResultsByTime']:
        for group in item['Groups']:
            instance_type = group['Keys']
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            if instance_type != ['NoInstanceType'] and amount > amount_threshold:
                currency = group['Metrics']['UnblendedCost']['Unit']
                message += f"A {instance_type[0]} instance cost {amount} {currency}\n"
                write_to_csv(instance_type[0], amount, currency, item['TimePeriod']['Start'], item['TimePeriod']['End'],
                             csv_report_filename)
    if message != '':
        logging.info('Found some expensive instances, sending report')
        client = boto3.client('sns')
        client.publish(
            TopicArn=topic_arn,
            Message=f'In the last 24 hours:\n{message}',
            Subject='Cost inspection report'
        )
        logging.info('Report sent')
    else:
        logging.info('No expensive instances found')


def main():
    try:
        profile_name = sys.argv[1]
        amount_threshold = float(sys.argv[2])
        sns_topic_arn = sys.argv[3]
        csv_report_filename = sys.argv[4]
    except IndexError:
        logging.error('Error parsing arguments')
        logging.info(
            'Usage: python3 cost_checker.py <profile_name> <amount_threshold> <sns_topic_arn> <csv_report_filename>')
        logging.info(
            'Example: python3 cost_checker.py costChecker1 100.5 "arn:aws:sns:eu-central-1:752594615588:CostReports"'
            ' cost_report.csv')
        sys.exit(2)
    time_format = '%Y-%m-%d'
    # get costs from yesterday to today
    start_date = (date.today() - timedelta(days=1)).strftime(time_format)
    end_date = date.today().strftime(time_format)
    boto3.setup_default_session(profile_name=profile_name)
    results = get_costs(start_date, end_date,
                        ['Amazon Elastic Compute Cloud - Compute', 'Amazon Relational Database Service'])
    generate_and_send_report(results, amount_threshold, sns_topic_arn, csv_report_filename)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    logging.info('Starting cost checker')
    main()
