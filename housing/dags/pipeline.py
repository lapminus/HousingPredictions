from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
from homeharvest import scrape_property


def acquire_data(location, listing_type, past_days, mls_only):
    properties = scrape_property(
        location=location,
        listing_type=listing_type,  # or (for_sale, for_rent, pending)
        past_days=past_days,  # sold in last 30 days - listed in last 30 days if (for_sale, for_rent)

        # date_from="2023-05-01", # alternative to past_days
        # date_to="2023-05-28",
        # foreclosure=True

        mls_only=mls_only,  # only fetch MLS listings
    )
    return properties


def clean_data(**kwargs):
    ti = kwargs['ti']
    properties = ti.xcom_pull(task_ids='acquire_data')

    # Convert address column to uppercase
    properties['street'] = properties['street'].str.upper()

    # Print rows with duplicated addresses before removing them
    duplicated_rows = properties[properties.duplicated(subset='street', keep='first')]
    if not duplicated_rows.empty:
        print("Rows with duplicated addresses:")
        print(duplicated_rows)

    # Remove duplicate rows based on the address column
    cleaned_properties = properties[~properties.duplicated(subset='street', keep='first')]

    print("Cleaning data completed")

    # Pass the cleaned properties data to the next task
    ti.xcom_push(key='cleaned_properties', value=cleaned_properties)

    return cleaned_properties


def store_data(**kwargs):
    ti = kwargs['ti']
    cleaned_properties = ti.xcom_pull(task_ids='clean_data', key='cleaned_properties')
    filename = kwargs['filename']

    # Save cleaned DataFrame to CSV
    cleaned_properties.to_csv(filename, index=False)
    print(f"Data stored in {filename}")


def analyze_data():
    print("Analyzing data..its ganna be mcgormiccck")
    return "brrrrr"


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 4, 1),
    'email_on_failure': False,
    'email_on_retry': False,
}

dag = DAG(
    'data_pipeline',
    default_args=default_args,
    description='Data pipeline for acquiring, cleaning, and storing properties data',
    schedule_interval=None,  # Set to None to trigger manually
)

acquire_data_task = PythonOperator(
    task_id='acquire_data',
    python_callable=acquire_data,
    op_kwargs={'location': "Los Angeles, CA", 'listing_type': "sold", 'past_days': 30, 'mls_only': True},
    provide_context=True,
    dag=dag,
)

clean_data_task = PythonOperator(
    task_id='clean_data',
    python_callable=clean_data,
    provide_context=True,
    dag=dag,
)

store_data_task = PythonOperator(
    task_id='store_data',
    python_callable=store_data,
    provide_context=True,
    op_kwargs={'filename': '/opt/airflow/data/cleaned_properties.csv'},
    dag=dag,
)

analyze_data_task = PythonOperator(
    task_id='analyze_data',
    python_callable=analyze_data,
    provide_context=True,
    dag=dag,
)

acquire_data_task >> clean_data_task >> store_data_task >> analyze_data_task
