import numpy as np

class OnlineARIMA:
    """
    Online ARIMA model for time series forecasting.

    Attributes:
    mk (int): Number of previous data points to use for forecasting (m + k).
    lrate (float): Learning rate for updating the model coefficients.
    w (numpy.ndarray): Coefficient vector for the model.
    epsilon (float): Small constant for numerical stability.
    A_trans (numpy.ndarray): Transformed matrix for gradient calculation.
    data_stream (list): List to store the time series data.
    forecast_data (list): List to store the forecasted values.
    """
    
    def __init__(self, mk=10, lrate=10**-1, init_w=None, epsilon=10**-4):
        """
        Initializes the OnlineARIMA model with the specified parameters.

        Parameters:
        mk (int): Number of previous data points to use for forecasting (m + k). Default is 10.
        lrate (float): Learning rate for updating the model coefficients. Default is 0.1.
        init_w (numpy.ndarray, optional): Initial coefficient vector for the model. If not provided, a random vector is initialized.
        epsilon (float): Small constant for numerical stability. Default is 10**-4.
        sampling_size (int): Size of the sampling window. Default is 1.
        """
        self.mk = mk
        self.lrate = lrate
        if init_w is None:
            init_w = np.random.rand(mk) / 1000
        self.w = np.array(init_w)
        self.epsilon = epsilon
        self.A_trans = np.eye(self.mk) * self.epsilon
        self.data_stream = []
        self.forecast_data = []

    def update_and_forecast(self, new_data):
        """
        Updates the model with new data and generates a forecast.

        Parameters:
        new_data (float): The new data point to be added to the time series.

        Returns:
        tuple: A tuple containing the forecasted value and a boolean indicating if the model was updated.
        """
        self.data_stream.append(new_data)
        if len(self.data_stream) > self.mk:
            prev_t = np.array(self.data_stream[-self.mk-1:-1])
            current_data = self.data_stream[-1] 
            if len(self.forecast_data) > 0:
                prev_forecast = self.forecast_data[-1]
            else:
                prev_forecast = np.dot(self.w, prev_t)
            diff = prev_forecast - current_data
            grad = 2 * prev_t * diff

            self.A_trans = self.A_trans - np.dot(self.A_trans, np.dot(grad.reshape(-1, 1), grad.reshape(1, -1))) * self.A_trans / (1 + grad.dot(self.A_trans.dot(grad)))
            self.w = self.w - self.lrate * grad.dot(self.A_trans)

            forecast = self.__forecast(np.array(self.data_stream[-self.mk:]))
            return forecast, True
        else:
            return new_data, False
            
    def __forecast(self, data):
        """
        Generates a forecast using the current model coefficients.

        Parameters:
        data (numpy.ndarray): The data points to be used for forecasting.

        Returns:
        float: The forecasted value.
        """
        forecast = np.dot(self.w, data)
        if forecast < 0:
            forecast = 0
        self.forecast_data.append(forecast)
        return forecast
