def prediction(stock, n_days):
    import yfinance as yf
    import numpy as np
    import pandas as pd
    from sklearn.model_selection import train_test_split, GridSearchCV
    from sklearn.svm import SVR
    from datetime import date, timedelta
    import plotly.graph_objs as go

    # Load the data
    df = yf.download(stock, period='1mo')
    
    # Check if data is empty
    if df.empty:
        raise ValueError("No data available for the stock symbol provided.")

    df.reset_index(inplace=True)
    df['Day'] = df.index

    # Prepare the dataset
    X = df[['Day']].values  # Feature: Day
    Y = df[['Close']].values  # Target: Close price

    # Split the dataset
    x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.1, shuffle=False)

    # Grid search for best SVR parameters
    gsc = GridSearchCV(
        estimator=SVR(kernel='rbf'),
        param_grid={
            'C': [0.001, 0.01, 0.1, 1, 100, 1000],
            'epsilon': [0.0001, 0.001, 0.01, 0.1, 1],
            'gamma': [0.0001, 0.001, 0.01, 0.1, 1]
        },
        cv=5,
        scoring='neg_mean_absolute_error',
        verbose=0,
        n_jobs=-1
    )

    # Flatten y_train for training
    y_train_flat = y_train.ravel()

    # Fit the model and get best parameters
    grid_result = gsc.fit(x_train, y_train_flat)
    best_svr = SVR(kernel='rbf', **grid_result.best_params_)

    # Train the best model
    best_svr.fit(x_train, y_train_flat)

    # Prepare output days for prediction
    output_days = [[i + x_test[-1][0]] for i in range(1, n_days + 1)]

    # Generate future dates
    future_dates = [date.today() + timedelta(days=i) for i in range(1, n_days + 1)]

    # Make predictions
    predictions = best_svr.predict(output_days)

    # Plot Results
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=future_dates, y=predictions, mode='lines+markers', name='Predicted Prices'))
    
    fig.update_layout(
        title=f"Predicted Close Price for the next {n_days} days",
        xaxis_title="Date",
        yaxis_title="Close Price"
    )

    return fig
