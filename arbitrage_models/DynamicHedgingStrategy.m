classdef DynamicHedgingStrategy < handle
    % DynamicHedgingStrategy Advanced dynamic hedging for multi-asset portfolios
    %   This class implements multi-dimensional hedging optimization for
    %   cross-asset arbitrage strategies.
    
    properties
        portfolio           % Current portfolio positions
        correlationMatrix   % Asset correlation matrix
        volatilities        % Asset volatility vector
        assetList           % List of assets
        hedgePositions      % Calculated hedge positions
        riskMatrix          % Risk matrix for optimization
        hedgingConstraints  % Constraints for hedging optimization
        hedgingCosts        % Transaction costs for hedging
        rebalanceThreshold  % Threshold for rebalancing hedges
    end
    
    methods
        function obj = DynamicHedgingStrategy()
            % Constructor for DynamicHedgingStrategy
            
            % Default rebalance threshold (5% deviation)
            obj.rebalanceThreshold = 0.05;
            
            % Default hedging constraints
            obj.hedgingConstraints = struct();
            obj.hedgingConstraints.maxLeverage = 3.0;
            obj.hedgingConstraints.minHedgeRatio = 0.7;
            obj.hedgingConstraints.maxPositionSize = 0.3;
            obj.hedgingConstraints.minLiquidity = 1000000;
            
            disp('DynamicHedgingStrategy initialized');
        end
        
        function setPortfolio(obj, portfolio, assetList)
            % Set current portfolio positions
            %
            % Args:
            %   portfolio: Vector of asset positions (positive=long, negative=short)
            %   assetList: Cell array of asset names/symbols
            
            obj.portfolio = portfolio(:);  % Ensure column vector
            obj.assetList = assetList;
            
            disp('Portfolio positions set');
        end
        
        function setMarketData(obj, correlationMatrix, volatilities)
            % Set market data for hedging calculations
            %
            % Args:
            %   correlationMatrix: Asset correlation matrix
            %   volatilities: Vector of asset volatilities
            
            obj.correlationMatrix = correlationMatrix;
            obj.volatilities = volatilities(:);  % Ensure column vector
            
            % Calculate risk matrix
            obj.riskMatrix = obj.calculateRiskMatrix();
            
            disp('Market data set');
        end
        
        function riskMatrix = calculateRiskMatrix(obj)
            % Calculate risk matrix from correlations and volatilities
            %
            % Returns:
            %   riskMatrix: Covariance matrix for portfolio optimization
            
            % Check if we have the necessary data
            if isempty(obj.correlationMatrix) || isempty(obj.volatilities)
                error('Correlation matrix and volatilities must be set first');
            end
            
            % Calculate covariance matrix
            volMatrix = diag(obj.volatilities);
            riskMatrix = volMatrix * obj.correlationMatrix * volMatrix;
            
            disp('Risk matrix calculated');
        end
        
        function hedging_positions = calculateDynamicHedge(obj, portfolio, correlations, volatilities)
            % Multi-dimensional hedging optimization
            %
            % Args:
            %   portfolio: Vector of asset positions to hedge
            %   correlations: Asset correlation matrix
            %   volatilities: Vector of asset volatilities
            %
            % Returns:
            %   hedging_positions: Optimal hedging positions
            
            % Use provided data or object properties
            if nargin < 2 || isempty(portfolio)
                portfolio = obj.portfolio;
            end
            
            if nargin < 3 || isempty(correlations)
                correlations = obj.correlationMatrix;
            end
            
            if nargin < 4 || isempty(volatilities)
                volatilities = obj.volatilities;
            end
            
            % Check if we have the necessary data
            if isempty(portfolio) || isempty(correlations) || isempty(volatilities)
                error('Portfolio, correlations, and volatilities must be set first');
            end
            
            % Calculate risk matrix
            volMatrix = diag(volatilities);
            risk_matrix = volMatrix * correlations * volMatrix;
            
            % Calculate optimal hedge positions
            % We use matrix inversion to find the hedge ratios that minimize variance
            try
                % Add small regularization term to ensure matrix is invertible
                reg_matrix = risk_matrix + eye(size(risk_matrix)) * 1e-6;
                hedging_positions = -inv(reg_matrix) * risk_matrix * portfolio;
            catch
                warning('Matrix inversion failed. Using pseudoinverse instead.');
                hedging_positions = -pinv(risk_matrix) * risk_matrix * portfolio;
            end
            
            % Apply hedging constraints
            hedging_positions = obj.applyHedgingConstraints(hedging_positions, portfolio);
            
            % Store results
            obj.hedgePositions = hedging_positions;
            
            disp('Dynamic hedge calculated');
        end
        
        function constrained_positions = applyHedgingConstraints(obj, hedge_positions, portfolio)
            % Apply constraints to hedge positions
            %
            % Args:
            %   hedge_positions: Calculated hedge positions
            %   portfolio: Original portfolio positions
            %
            % Returns:
            %   constrained_positions: Hedge positions after applying constraints
            
            % Start with unconstrained positions
            constrained_positions = hedge_positions;
            
            % Calculate portfolio value (absolute sum)
            portfolio_value = sum(abs(portfolio));
            
            % Apply maximum position size constraint
            max_position = portfolio_value * obj.hedgingConstraints.maxPositionSize;
            for i = 1:length(constrained_positions)
                if abs(constrained_positions(i)) > max_position
                    constrained_positions(i) = sign(constrained_positions(i)) * max_position;
                end
            end
            
            % Apply maximum leverage constraint
            total_exposure = sum(abs(portfolio)) + sum(abs(constrained_positions));
            max_allowed_exposure = portfolio_value * obj.hedgingConstraints.maxLeverage;
            
            if total_exposure > max_allowed_exposure
                scale_factor = (max_allowed_exposure - sum(abs(portfolio))) / sum(abs(constrained_positions));
                constrained_positions = constrained_positions * scale_factor;
            end
            
            % Apply minimum hedge ratio constraint
            portfolio_risk = sqrt(portfolio' * obj.riskMatrix * portfolio);
            hedged_portfolio = portfolio + constrained_positions;
            hedged_risk = sqrt(hedged_portfolio' * obj.riskMatrix * hedged_portfolio);
            
            min_required_risk_reduction = portfolio_risk * obj.hedgingConstraints.minHedgeRatio;
            
            if hedged_risk > portfolio_risk - min_required_risk_reduction
                % If hedge is not effective enough, scale it up
                target_risk = portfolio_risk - min_required_risk_reduction;
                if target_risk < 0
                    target_risk = 0;  % Can't reduce below zero
                end
                
                % Try to find a scaling factor that achieves the target risk
                % This is a simplified approach; a more sophisticated optimization could be used
                scale_factor = 1.0;
                max_scale = 5.0;  % Limit scaling to prevent extreme positions
                step = 0.1;
                
                while scale_factor < max_scale
                    test_positions = constrained_positions * scale_factor;
                    test_portfolio = portfolio + test_positions;
                    test_risk = sqrt(test_portfolio' * obj.riskMatrix * test_portfolio);
                    
                    if test_risk <= target_risk
                        constrained_positions = test_positions;
                        break;
                    end
                    
                    scale_factor = scale_factor + step;
                end
            end
            
            disp('Hedging constraints applied');
        end
        
        function [rebalance_needed, deviation] = checkRebalanceNeeded(obj, current_prices)
            % Check if hedge rebalancing is needed based on price changes
            %
            % Args:
            %   current_prices: Vector of current asset prices
            %
            % Returns:
            %   rebalance_needed: Boolean indicating if rebalance is needed
            %   deviation: Maximum deviation from optimal hedge
            
            if isempty(obj.hedgePositions) || isempty(obj.portfolio)
                error('Portfolio and hedge positions must be calculated first');
            end
            
            % Calculate optimal hedge with current market data
            optimal_hedge = obj.calculateDynamicHedge();
            
            % Calculate relative deviation from optimal hedge
            deviation = abs(optimal_hedge - obj.hedgePositions) ./ (abs(obj.hedgePositions) + 1e-6);
            max_deviation = max(deviation);
            
            % Determine if rebalance is needed
            rebalance_needed = max_deviation > obj.rebalanceThreshold;
            
            if rebalance_needed
                disp(['Hedge rebalance needed. Maximum deviation: ', num2str(max_deviation*100), '%']);
            else
                disp(['Hedge rebalance not needed. Maximum deviation: ', num2str(max_deviation*100), '%']);
            end
        end
        
        function cost = estimateHedgingCost(obj, current_positions, target_positions, prices, spreads)
            % Estimate cost of adjusting hedge positions
            %
            % Args:
            %   current_positions: Current hedge positions
            %   target_positions: Target hedge positions
            %   prices: Current asset prices
            %   spreads: Bid-ask spreads as percentage of price
            %
            % Returns:
            %   cost: Estimated cost of hedge adjustment
            
            % Calculate position changes
            position_changes = target_positions - current_positions;
            
            % Calculate transaction costs based on spreads
            half_spreads = spreads / 2;  % Half spread for each side of transaction
            cost = sum(abs(position_changes) .* prices .* half_spreads);
            
            obj.hedgingCosts = cost;
            
            disp(['Estimated hedging cost: $', num2str(cost)]);
        end
        
        function visualizeHedgeEffectiveness(obj)
            % Visualize the effectiveness of the hedge in reducing risk
            
            if isempty(obj.portfolio) || isempty(obj.hedgePositions) || isempty(obj.riskMatrix)
                error('Portfolio, hedge positions, and risk matrix must be set first');
            end
            
            % Calculate unhedged portfolio risk
            unhedged_risk = sqrt(obj.portfolio' * obj.riskMatrix * obj.portfolio);
            
            % Calculate hedged portfolio risk
            hedged_portfolio = obj.portfolio + obj.hedgePositions;
            hedged_risk = sqrt(hedged_portfolio' * obj.riskMatrix * hedged_portfolio);
            
            % Calculate risk reduction percentage
            risk_reduction = (unhedged_risk - hedged_risk) / unhedged_risk * 100;
            
            % Create bar chart
            figure;
            bar([unhedged_risk, hedged_risk]);
            set(gca, 'XTickLabel', {'Unhedged', 'Hedged'});
            ylabel('Portfolio Risk');
            title(['Hedge Effectiveness: ', num2str(risk_reduction), '% Risk Reduction']);
            
            % Add text labels
            text(1, unhedged_risk/2, num2str(unhedged_risk, '%.2f'), 'HorizontalAlignment', 'center');
            text(2, hedged_risk/2, num2str(hedged_risk, '%.2f'), 'HorizontalAlignment', 'center');
            
            disp(['Hedge reduces portfolio risk by ', num2str(risk_reduction), '%']);
        end
    end
end