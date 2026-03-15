classdef PredictiveAnalytics < handle
    % PredictiveAnalytics Advanced predictive models for price forecasting
    %   This class implements LSTM neural networks, regime change detection,
    %   and volatility surface modeling for predictive analytics.
    
    properties
        priceData           % Historical price data
        timeStamps          % Time stamps for historical data
        assetList           % List of assets
        lstmModels          % LSTM neural network models
        regimeModels        % Regime change detection models
        volatilitySurface   % Volatility surface models
        predictionHorizons  % Prediction time horizons
        trainingConfig      % Neural network training configuration
        regimeStates        % Current regime states for each asset
        lastUpdate          % Last update timestamp
        predictionResults   % Latest prediction results
    end
    
    methods
        function obj = PredictiveAnalytics()
            % Constructor for PredictiveAnalytics
            
            % Default prediction horizons (in minutes)
            obj.predictionHorizons = [5, 15, 30, 60, 240];
            
            % Default training configuration
            obj.trainingConfig = struct();
            obj.trainingConfig.maxEpochs = 250;
            obj.trainingConfig.miniBatchSize = 32;
            obj.trainingConfig.initialLearnRate = 0.005;
            obj.trainingConfig.learnRateDropFactor = 0.2;
            obj.trainingConfig.learnRateDropPeriod = 50;
            obj.trainingConfig.gradientThreshold = 1;
            obj.trainingConfig.validationFrequency = 50;
            obj.trainingConfig.validationPatience = 10;
            
            obj.lastUpdate = datetime('now');
            
            disp('PredictiveAnalytics initialized');
        end
        
        function loadData(obj, priceData, timeStamps, assetList)
            % Load historical price data
            %
            % Args:
            %   priceData: Matrix of historical price data (rows=time, cols=assets)
            %   timeStamps: Vector of datetime objects for each data point
            %   assetList: Cell array of asset names/symbols
            
            obj.priceData = priceData;
            obj.timeStamps = timeStamps;
            obj.assetList = assetList;
            
            % Initialize model containers
            obj.lstmModels = cell(length(assetList), length(obj.predictionHorizons));
            obj.regimeModels = cell(length(assetList), 1);
            obj.volatilitySurface = cell(length(assetList), 1);
            obj.regimeStates = zeros(length(assetList), 1);
            
            disp('Data loaded successfully');
        end
        
        function trainLSTMModels(obj, assetIndices, sequenceLength)
            % Train LSTM neural networks for price prediction
            %
            % Args:
            %   assetIndices: Indices of assets to train models for (default: all)
            %   sequenceLength: Length of input sequences for LSTM (default: 60)
            
            if nargin < 2 || isempty(assetIndices)
                assetIndices = 1:length(obj.assetList);
            end
            
            if nargin < 3
                sequenceLength = 60;
            end
            
            if isempty(obj.priceData)
                error('Price data must be loaded first');
            end
            
            % Loop through each selected asset
            for i = 1:length(assetIndices)
                assetIdx = assetIndices(i);
                assetName = obj.assetList{assetIdx};
                disp(['Training LSTM models for ', assetName, '...']);
                
                % Extract price data for this asset
                prices = obj.priceData(:, assetIdx);
                
                % Loop through each prediction horizon
                for j = 1:length(obj.predictionHorizons)
                    horizon = obj.predictionHorizons(j);
                    disp(['  Horizon: ', num2str(horizon), ' minutes']);
                    
                    % Prepare training data
                    [X, Y] = obj.prepareTimeSeriesData(prices, sequenceLength, horizon);
                    
                    % Create and train LSTM network
                    model = obj.createLSTMNetwork(sequenceLength);
                    
                    % Train the model
                    try
                        model = obj.trainModel(model, X, Y);
                        obj.lstmModels{assetIdx, j} = model;
                        disp(['    Model trained successfully']);
                    catch e
                        warning(['    Failed to train model: ', e.message]);
                    end
                end
            end
            
            obj.lastUpdate = datetime('now');
            disp('LSTM model training completed');
        end
        
        function [X, Y] = prepareTimeSeriesData(obj, prices, sequenceLength, horizon)
            % Prepare time series data for LSTM training
            %
            % Args:
            %   prices: Vector of historical prices
            %   sequenceLength: Length of input sequences
            %   horizon: Prediction horizon (how many steps ahead to predict)
            %
            % Returns:
            %   X: Input sequences (3D array: samples x features x timesteps)
            %   Y: Target values (vector)
            
            % Normalize prices
            normalizedPrices = (prices - mean(prices)) / std(prices);
            
            % Calculate returns
            returns = diff(normalizedPrices) ./ normalizedPrices(1:end-1);
            
            % Add features (returns, moving averages, etc.)
            features = zeros(length(returns), 3);
            features(:, 1) = returns;
            
            % 5-period moving average of returns
            ma5 = movmean(returns, 5);
            features(:, 2) = ma5;
            
            % 20-period moving average of returns
            ma20 = movmean(returns, 20);
            features(:, 3) = ma20;
            
            % Create sequences
            numSamples = length(features) - sequenceLength - horizon + 1;
            X = zeros(numSamples, 3, sequenceLength);
            Y = zeros(numSamples, 1);
            
            for i = 1:numSamples
                X(i, :, :) = features(i:i+sequenceLength-1, :)';
                Y(i) = normalizedPrices(i+sequenceLength+horizon-1);
            end
        end
        
        function model = createLSTMNetwork(obj, sequenceLength)
            % Create LSTM neural network architecture
            %
            % Args:
            %   sequenceLength: Length of input sequences
            %
            % Returns:
            %   model: LSTM neural network model
            
            % Define LSTM network architecture
            layers = [
                sequenceInputLayer(3)
                lstmLayer(50, 'OutputMode', 'last')
                fullyConnectedLayer(25)
                reluLayer
                dropoutLayer(0.2)
                fullyConnectedLayer(1)
                regressionLayer
            ];
            
            % Define training options
            options = trainingOptions('adam', ...
                'MaxEpochs', obj.trainingConfig.maxEpochs, ...
                'MiniBatchSize', obj.trainingConfig.miniBatchSize, ...
                'InitialLearnRate', obj.trainingConfig.initialLearnRate, ...
                'LearnRateSchedule', 'piecewise', ...
                'LearnRateDropFactor', obj.trainingConfig.learnRateDropFactor, ...
                'LearnRateDropPeriod', obj.trainingConfig.learnRateDropPeriod, ...
                'GradientThreshold', obj.trainingConfig.gradientThreshold, ...
                'ValidationFrequency', obj.trainingConfig.validationFrequency, ...
                'ValidationPatience', obj.trainingConfig.validationPatience, ...
                'Shuffle', 'every-epoch', ...
                'Verbose', false, ...
                'Plots', 'none');
            
            % Create model
            model = struct('layers', layers, 'options', options);
        end
        
        function model = trainModel(obj, model, X, Y)
            % Train neural network model
            %
            % Args:
            %   model: Neural network model structure
            %   X: Input data
            %   Y: Target data
            %
            % Returns:
            %   model: Trained neural network model
            
            % Split data into training and validation sets
            numSamples = size(X, 1);
            trainRatio = 0.8;
            trainIdx = 1:floor(numSamples * trainRatio);
            valIdx = floor(numSamples * trainRatio)+1:numSamples;
            
            XTrain = X(trainIdx, :, :);
            YTrain = Y(trainIdx);
            XVal = X(valIdx, :, :);
            YVal = Y(valIdx);
            
            % Train the network
            net = trainNetwork(XTrain, YTrain, model.layers, model.options);
            
            % Add trained network to model structure
            model.net = net;
            
            % Evaluate on validation set
            YPred = predict(net, XVal);
            mse = mean((YPred - YVal).^2);
            model.validationMSE = mse;
            
            disp(['    Validation MSE: ', num2str(mse)]);
        end
        
        function detectRegimeChanges(obj, assetIndices, windowSize)
            % Detect regime changes in asset price dynamics
            %
            % Args:
            %   assetIndices: Indices of assets to analyze (default: all)
            %   windowSize: Size of rolling window for regime detection (default: 60)
            
            if nargin < 2 || isempty(assetIndices)
                assetIndices = 1:length(obj.assetList);
            end
            
            if nargin < 3
                windowSize = 60;
            end
            
            if isempty(obj.priceData)
                error('Price data must be loaded first');
            end
            
            % Loop through each selected asset
            for i = 1:length(assetIndices)
                assetIdx = assetIndices(i);
                assetName = obj.assetList{assetIdx};
                disp(['Detecting regime changes for ', assetName, '...']);
                
                % Extract price data for this asset
                prices = obj.priceData(:, assetIdx);
                
                % Calculate returns
                returns = diff(prices) ./ prices(1:end-1);
                
                % Initialize regime model
                regimeModel = struct();
                regimeModel.windowSize = windowSize;
                regimeModel.numRegimes = 3;  % Low, medium, high volatility
                
                % Detect regimes using Hidden Markov Model
                try
                    % Calculate rolling volatility
                    rollingVol = movstd(returns, windowSize);
                    
                    % Fit Gaussian Mixture Model to identify regimes
                    gmm = fitgmdist(rollingVol, regimeModel.numRegimes, 'RegularizationValue', 0.01);
                    regimeModel.gmm = gmm;
                    
                    % Classify current regime
                    currentVol = std(returns(end-windowSize+1:end));
                    [~, regimeProbs] = posterior(gmm, currentVol);
                    [~, currentRegime] = max(regimeProbs);
                    
                    % Store results
                    regimeModel.regimeProbs = regimeProbs;
                    regimeModel.currentRegime = currentRegime;
                    obj.regimeModels{assetIdx} = regimeModel;
                    obj.regimeStates(assetIdx) = currentRegime;
                    
                    disp(['  Current regime: ', num2str(currentRegime), ' (', ...
                          'Probability: ', num2str(regimeProbs(currentRegime)*100), '%)']);
                catch e
                    warning(['  Failed to detect regimes: ', e.message]);
                end
            end
            
            disp('Regime change detection completed');
        end
        
        function modelVolatilitySurface(obj, assetIndices, timePoints, strikePoints)
            % Model volatility surface for option pricing and risk analysis
            %
            % Args:
            %   assetIndices: Indices of assets to model (default: all)
            %   timePoints: Vector of time points for surface (in days)
            %   strikePoints: Vector of strike price ratios for surface
            
            if nargin < 2 || isempty(assetIndices)
                assetIndices = 1:length(obj.assetList);
            end
            
            if nargin < 3
                timePoints = [1, 7, 30, 90, 180, 365];  % Days to expiration
            end
            
            if nargin < 4
                strikePoints = 0.8:0.05:1.2;  % Strike price / current price
            end
            
            if isempty(obj.priceData)
                error('Price data must be loaded first');
            end
            
            % Loop through each selected asset
            for i = 1:length(assetIndices)
                assetIdx = assetIndices(i);
                assetName = obj.assetList{assetIdx};
                disp(['Modeling volatility surface for ', assetName, '...']);
                
                % Extract price data for this asset
                prices = obj.priceData(:, assetIdx);
                
                % Calculate returns
                returns = diff(prices) ./ prices(1:end-1);
                
                % Calculate historical volatility (annualized)
                historicalVol = std(returns) * sqrt(365);
                
                % Create volatility surface model
                volModel = struct();
                volModel.timePoints = timePoints;
                volModel.strikePoints = strikePoints;
                volModel.surface = zeros(length(timePoints), length(strikePoints));
                
                % Generate synthetic volatility surface with smile/skew
                for t = 1:length(timePoints)
                    timeFactor = sqrt(timePoints(t) / 365);
                    for s = 1:length(strikePoints)
                        strike = strikePoints(s);
                        
                        % Create volatility smile/skew effect
                        if strike < 1.0
                            % Out-of-the-money puts (higher vol)
                            skewFactor = 1.0 + 0.2 * (1.0 - strike)^2;
                        else
                            % Out-of-the-money calls (lower vol)
                            skewFactor = 1.0 + 0.1 * (strike - 1.0)^2;
                        end
                        
                        % Term structure effect (longer term = more mean reversion)
                        termFactor = 1.0 - 0.1 * log(timePoints(t) / 30);
                        termFactor = max(0.8, min(1.2, termFactor));
                        
                        % Combine effects
                        volModel.surface(t, s) = historicalVol * skewFactor * termFactor;
                    end
                end
                
                % Store model
                obj.volatilitySurface{assetIdx} = volModel;
                
                disp(['  Volatility surface modeled successfully']);
            end
            
            disp('Volatility surface modeling completed');
        end
        
        function predictions = predictPrices(obj, assetIndices, currentData, horizonIndices)
            % Predict future prices using trained LSTM models
            %
            % Args:
            %   assetIndices: Indices of assets to predict (default: all)
            %   currentData: Current market data for prediction
            %   horizonIndices: Indices of prediction horizons to use (default: all)
            %
            % Returns:
            %   predictions: Structure with prediction results
            
            if nargin < 2 || isempty(assetIndices)
                assetIndices = 1:length(obj.assetList);
            end
            
            if nargin < 4 || isempty(horizonIndices)
                horizonIndices = 1:length(obj.predictionHorizons);
            end
            
            % Initialize predictions structure
            predictions = struct();
            predictions.assets = cell(length(assetIndices), 1);
            predictions.horizons = obj.predictionHorizons(horizonIndices);
            predictions.values = zeros(length(assetIndices), length(horizonIndices));
            predictions.confidence = zeros(length(assetIndices), length(horizonIndices));
            predictions.regimes = zeros(length(assetIndices), 1);
            predictions.timestamp = datetime('now');
            
            % Loop through each selected asset
            for i = 1:length(assetIndices)
                assetIdx = assetIndices(i);
                predictions.assets{i} = obj.assetList{assetIdx};
                
                % Get current regime if available
                if ~isempty(obj.regimeModels) && ~isempty(obj.regimeModels{assetIdx})
                    predictions.regimes(i) = obj.regimeStates(assetIdx);
                end
                
                % Loop through each prediction horizon
                for j = 1:length(horizonIndices)
                    horizonIdx = horizonIndices(j);
                    
                    % Check if model exists
                    if isempty(obj.lstmModels) || isempty(obj.lstmModels{assetIdx, horizonIdx})
                        predictions.values(i, j) = NaN;
                        predictions.confidence(i, j) = 0;
                        continue;
                    end
                    
                    % Get model
                    model = obj.lstmModels{assetIdx, horizonIdx};
                    
                    % Prepare input data
                    % This is a simplified version - in practice, you would need to
                    % prepare the input data in the same way as during training
                    inputData = currentData(assetIdx, :, :);
                    
                    % Make prediction
                    try
                        predictedValue = predict(model.net, inputData);
                        predictions.values(i, j) = predictedValue;
                        
                        % Set confidence based on validation error
                        if isfield(model, 'validationMSE')
                            predictions.confidence(i, j) = 1 / (1 + model.validationMSE);
                        else
                            predictions.confidence(i, j) = 0.5;  % Default confidence
                        end
                    catch
                        predictions.values(i, j) = NaN;
                        predictions.confidence(i, j) = 0;
                    end
                end
            end
            
            % Store prediction results
            obj.predictionResults = predictions;
            
            disp('Price predictions completed');
        end
        
        function visualizeVolatilitySurface(obj, assetIdx)
            % Visualize volatility surface for a specific asset
            %
            % Args:
            %   assetIdx: Index of asset to visualize
            
            if isempty(obj.volatilitySurface) || isempty(obj.volatilitySurface{assetIdx})
                error('Volatility surface must be modeled first');
            end
            
            % Get volatility surface model
            volModel = obj.volatilitySurface{assetIdx};
            
            % Create meshgrid for surface
            [X, Y] = meshgrid(volModel.strikePoints, volModel.timePoints);
            
            % Create 3D surface plot
            figure;
            surf(X, Y, volModel.surface);
            
            % Set labels and title
            xlabel('Strike Price Ratio');
            ylabel('Days to Expiration');
            zlabel('Implied Volatility');
            title(['Volatility Surface for ', obj.assetList{assetIdx}]);
            
            % Add colorbar
            colorbar;
            
            % Adjust view
            view(45, 30);
        end
        
        function visualizePredictions(obj, assetIndices, horizonIndices)
            % Visualize price predictions for selected assets and horizons
            %
            % Args:
            %   assetIndices: Indices of assets to visualize
            %   horizonIndices: Indices of prediction horizons to visualize
            
            if isempty(obj.predictionResults)
                error('Predictions must be generated first');
            end
            
            if nargin < 2 || isempty(assetIndices)
                assetIndices = 1:length(obj.predictionResults.assets);
            end
            
            if nargin < 3 || isempty(horizonIndices)
                horizonIndices = 1:length(obj.predictionResults.horizons);
            end
            
            % Create figure
            figure;
            
            % Loop through each selected asset
            for i = 1:length(assetIndices)
                assetIdx = assetIndices(i);
                assetName = obj.predictionResults.assets{assetIdx};
                
                % Create subplot
                subplot(length(assetIndices), 1, i);
                
                % Extract prediction values and horizons
                horizons = obj.predictionResults.horizons(horizonIndices);
                values = obj.predictionResults.values(assetIdx, horizonIndices);
                confidence = obj.predictionResults.confidence(assetIdx, horizonIndices);
                
                % Plot predictions
                errorbar(horizons, values, (1-confidence).*abs(values), 'o-');
                
                % Add labels
                xlabel('Prediction Horizon (minutes)');
                ylabel('Predicted Price');
                title(['Price Predictions for ', assetName]);
                
                % Add grid
                grid on;
            end
        end
    end
end