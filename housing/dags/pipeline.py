from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
from homeharvest import scrape_property
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import pandas as pd

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

def analyze_data(**kwargs):
    ti = kwargs['ti']
    cleaned_properties = ti.xcom_pull(task_ids='clean_data', key='cleaned_properties')
    filename = kwargs['filename']
    cleaned_properties_df = pd.read_csv(filename)

    if cleaned_properties_df.empty:
        print("No data to analyze")
        return
    
    # Display statistical summaries of the sold prices
    sold_prices = cleaned_properties_df['sold_price']

    # Ensure the 'sold_price' column is treated as numeric
    sold_prices = pd.to_numeric(sold_prices, errors='coerce')

    # Get descriptive statistics
    summary_stats = sold_prices.describe()

    # Calculate additional statistics
    min_price = sold_prices.min()
    max_price = sold_prices.max()
    median_price = sold_prices.median()
    mean_price = sold_prices.mean()
    std_dev_price = sold_prices.std()

    summary = {
        'summary_stats': summary_stats,
        'min_price': min_price,
        'max_price': max_price,
        'median_price': median_price,
        'mean_price': mean_price,
    }

    # Print the statistics
    print(f"Summary Statistics:\n{summary_stats}\n")
    print(f"Min Price: {min_price}")
    print(f"Max Price: {max_price}")
    print(f"Median Price: {median_price}")
    print(f"Mean Price: {mean_price}")
    print(f"Standard Deviation: {std_dev_price}")

    # Select relevant features for training
    features = ['beds', 'full_baths', 'half_baths', 'sqft', 'year_built', 'lot_sqft',
                'price_per_sqft', 'stories', 'hoa_fee', 'parking_garage', 'list_price',
                'assessed_value', 'estimated_value']

    # Drop rows with missing target values (sold_price)
    cleaned_properties.dropna(subset=['sold_price'], inplace=True)

    # Prepare data for modeling
    X = cleaned_properties[features]
    y = cleaned_properties['sold_price']

    # Split data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Define and train the model (Random Forest Regressor)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate the model
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = mse ** 0.5
    print(f"Root Mean Squared Error (RMSE): {rmse}")

    # Store or output model evaluation results
    evaluation_results = {
        'RMSE': rmse,
        'model_name': 'RandomForestRegressor',
        'model_params': {
            'n_estimators': 100,
            'random_state': 42
        }
    }
    # You can push evaluation results to XCom for monitoring or further use
    ti.xcom_push(key='evaluation_results', value=evaluation_results)

    return evaluation_results


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
    op_kwargs={'filename': '/opt/airflow/data/cleaned_properties.csv'},
    dag=dag,
)

acquire_data_task >> clean_data_task >> store_data_task >> analyze_data_task
