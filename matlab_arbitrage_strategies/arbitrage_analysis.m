
function run_arbitrage_analysis()
    % Enhanced MATLAB Arbitrage Strategy Analysis
    fprintf('=== MATLAB Arbitrage Strategy Analysis ===\n');
    
    try
        % Load data
        fprintf('Loading market data...\n');
        data = readtable('market_data.csv');
        
        % Initialize results structure
        results = struct();
        results.timestamp = datestr(now);
        results.total_opportunities = height(data);
        
        % Extract key variables
        price_spread = data.price_spread;
        volatility = data.volatility; 
        gas_cost = data.gas_cost;
        liquidity = data.liquidity_score;
        actual_profit = data.profit;
        
        fprintf('Data loaded: %d arbitrage opportunities\n', length(price_spread));
        
        %% Strategy 1: Statistical Arbitrage (Mean Reversion)
        fprintf('\n--- Statistical Arbitrage Strategy ---\n');
        
        % Calculate z-scores for mean reversion
        window = min(20, floor(length(price_spread)/3));
        spread_ma = movmean(price_spread, window);
        spread_std = movstd(price_spread, window);
        z_scores = (price_spread - spread_ma) ./ (spread_std + 1e-8);
        
        % Generate signals
        stat_signals = zeros(size(z_scores));
        stat_signals(z_scores > 2.0) = -1;  % Short overpriced
        stat_signals(z_scores < -2.0) = 1;  % Long underpriced
        
        % Calculate strategy returns
        stat_returns = stat_signals .* actual_profit;
        valid_trades = stat_signals ~= 0;
        
        results.statistical = struct();
        results.statistical.total_trades = sum(valid_trades);
        results.statistical.total_return = sum(stat_returns);
        results.statistical.avg_return = mean(stat_returns(valid_trades));
        results.statistical.win_rate = sum(stat_returns > 0) / sum(valid_trades) * 100;
        results.statistical.sharpe = calculate_sharpe(stat_returns);
        results.statistical.max_drawdown = calculate_max_drawdown(cumsum(stat_returns));
        
        fprintf('Statistical Arbitrage Results:\n');
        fprintf('  Trades: %d\n', results.statistical.total_trades);
        fprintf('  Total Return: $%.4f\n', results.statistical.total_return);
        fprintf('  Win Rate: %.1f%%\n', results.statistical.win_rate);
        fprintf('  Sharpe Ratio: %.3f\n', results.statistical.sharpe);
        
        %% Strategy 2: Momentum-Based Arbitrage
        fprintf('\n--- Momentum Arbitrage Strategy ---\n');
        
        % Calculate momentum indicators
        short_window = max(3, floor(window/4));
        long_window = window;
        
        short_ma = movmean(price_spread, short_window);
        long_ma = movmean(price_spread, long_window);
        momentum = short_ma - long_ma;
        
        % Momentum signals
        mom_threshold = std(momentum) * 1.2;
        mom_signals = zeros(size(momentum));
        mom_signals(momentum > mom_threshold) = 1;
        mom_signals(momentum < -mom_threshold) = -1;
        
        % Calculate returns
        mom_returns = mom_signals .* actual_profit;
        mom_valid = mom_signals ~= 0;
        
        results.momentum = struct();
        results.momentum.total_trades = sum(mom_valid);
        results.momentum.total_return = sum(mom_returns);
        results.momentum.avg_return = mean(mom_returns(mom_valid));
        results.momentum.win_rate = sum(mom_returns > 0) / sum(mom_valid) * 100;
        results.momentum.sharpe = calculate_sharpe(mom_returns);
        results.momentum.max_drawdown = calculate_max_drawdown(cumsum(mom_returns));
        
        fprintf('Momentum Arbitrage Results:\n');
        fprintf('  Trades: %d\n', results.momentum.total_trades);
        fprintf('  Total Return: $%.4f\n', results.momentum.total_return);
        fprintf('  Win Rate: %.1f%%\n', results.momentum.win_rate);
        fprintf('  Sharpe Ratio: %.3f\n', results.momentum.sharpe);
        
        %% Strategy 3: Volatility-Adjusted Arbitrage
        fprintf('\n--- Volatility-Adjusted Arbitrage ---\n');
        
        % Volatility-based position sizing
        vol_ma = movmean(volatility, window);
        vol_zscore = (volatility - vol_ma) ./ (movstd(volatility, window) + 1e-8);
        
        % Adjust position sizes based on volatility
        vol_positions = zeros(size(volatility));
        
        % High volatility = smaller positions
        % Low volatility = larger positions
        base_position = 1.0;
        vol_positions = base_position ./ (1 + abs(vol_zscore));
        
        % Apply to profitable opportunities only
        profitable_ops = actual_profit > 0;
        vol_signals = profitable_ops .* vol_positions;
        
        vol_returns = vol_signals .* actual_profit;
        vol_valid = vol_signals > 0;
        
        results.volatility = struct();
        results.volatility.total_trades = sum(vol_valid);
        results.volatility.total_return = sum(vol_returns);
        results.volatility.avg_return = mean(vol_returns(vol_valid));
        results.volatility.win_rate = sum(vol_returns > 0) / sum(vol_valid) * 100;
        results.volatility.sharpe = calculate_sharpe(vol_returns);
        results.volatility.max_drawdown = calculate_max_drawdown(cumsum(vol_returns));
        
        fprintf('Volatility-Adjusted Results:\n');
        fprintf('  Trades: %d\n', results.volatility.total_trades);
        fprintf('  Total Return: $%.4f\n', results.volatility.total_return);
        fprintf('  Win Rate: %.1f%%\n', results.volatility.win_rate);
        fprintf('  Sharpe Ratio: %.3f\n', results.volatility.sharpe);
        
        %% Portfolio Optimization
        fprintf('\n--- Portfolio Optimization ---\n');
        
        % Combine strategies with optimal weights
        strategy_returns = [stat_returns, mom_returns, vol_returns];
        
        % Calculate correlation matrix
        corr_matrix = corrcoef(strategy_returns);
        
        % Simple equal-weight portfolio
        portfolio_returns = mean(strategy_returns, 2);
        port_valid = any(strategy_returns ~= 0, 2);
        
        results.portfolio = struct();
        results.portfolio.total_trades = sum(port_valid);
        results.portfolio.total_return = sum(portfolio_returns);
        results.portfolio.avg_return = mean(portfolio_returns(port_valid));
        results.portfolio.win_rate = sum(portfolio_returns > 0) / sum(port_valid) * 100;
        results.portfolio.sharpe = calculate_sharpe(portfolio_returns);
        results.portfolio.max_drawdown = calculate_max_drawdown(cumsum(portfolio_returns));
        
        fprintf('Portfolio Results:\n');
        fprintf('  Total Return: $%.4f\n', results.portfolio.total_return);
        fprintf('  Win Rate: %.1f%%\n', results.portfolio.win_rate);
        fprintf('  Sharpe Ratio: %.3f\n', results.portfolio.sharpe);
        
        %% Current Market Signals
        fprintf('\n--- Current Market Analysis ---\n');
        
        % Latest signals
        current_stat = stat_signals(end);
        current_mom = mom_signals(end);
        current_vol = vol_signals(end);
        
        results.current_signals = struct();
        results.current_signals.statistical = current_stat;
        results.current_signals.momentum = current_mom;
        results.current_signals.volatility_position = current_vol;
        
        % Overall recommendation
        signal_strength = abs(current_stat) + abs(current_mom) + (current_vol > 0.5);
        
        if signal_strength >= 2.5
            recommendation = 'STRONG_EXECUTE';
        elseif signal_strength >= 1.5
            recommendation = 'EXECUTE';
        elseif signal_strength >= 0.5
            recommendation = 'MONITOR';
        else
            recommendation = 'WAIT';
        end
        
        results.current_signals.recommendation = recommendation;
        results.current_signals.confidence = signal_strength / 3.0;
        
        fprintf('Current Signals:\n');
        fprintf('  Statistical: %.0f\n', current_stat);
        fprintf('  Momentum: %.0f\n', current_mom);
        fprintf('  Vol Position: %.3f\n', current_vol);
        fprintf('  Recommendation: %s\n', recommendation);
        fprintf('  Confidence: %.1f%%\n', results.current_signals.confidence * 100);
        
        %% Save Results
        fprintf('\n--- Saving Results ---\n');
        
        % Save to MAT file
        save('results/matlab_arbitrage_results.mat', 'results');
        fprintf('Results saved to: results/matlab_arbitrage_results.mat\n');
        
        % Create comprehensive report
        create_arbitrage_report(results);
        
        fprintf('\n=== MATLAB Analysis Complete ===\n');
        
    catch ME
        fprintf('ERROR in MATLAB analysis: %s\n', ME.message);
        fprintf('Error occurred in: %s\n', ME.stack(1).name);
        
        % Save error info
        error_info = struct();
        error_info.message = ME.message;
        error_info.timestamp = datestr(now);
        save('results/error_log.mat', 'error_info');
    end
end

function sharpe = calculate_sharpe(returns)
    if std(returns) == 0
        sharpe = 0;
    else
        sharpe = mean(returns) / std(returns) * sqrt(252); % Annualized
    end
end

function max_dd = calculate_max_drawdown(cumulative_returns)
    running_max = cummax(cumulative_returns);
    drawdowns = cumulative_returns - running_max;
    max_dd = min(drawdowns);
end

function create_arbitrage_report(results)
    % Create comprehensive text report
    report_file = 'results/arbitrage_strategy_report.txt';
    fid = fopen(report_file, 'w');
    
    fprintf(fid, '========================================\n');
    fprintf(fid, 'MATLAB ARBITRAGE STRATEGY ANALYSIS\n');
    fprintf(fid, '========================================\n');
    fprintf(fid, 'Generated: %s\n', results.timestamp);
    fprintf(fid, 'Total Opportunities Analyzed: %d\n\n', results.total_opportunities);
    
    fprintf(fid, 'STRATEGY PERFORMANCE SUMMARY:\n');
    fprintf(fid, '----------------------------\n\n');
    
    % Statistical Arbitrage
    fprintf(fid, '1. STATISTICAL ARBITRAGE (Mean Reversion)\n');
    fprintf(fid, '   Trades Executed: %d\n', results.statistical.total_trades);
    fprintf(fid, '   Total Return: $%.4f\n', results.statistical.total_return);
    fprintf(fid, '   Average Return: $%.4f\n', results.statistical.avg_return);
    fprintf(fid, '   Win Rate: %.1f%%\n', results.statistical.win_rate);
    fprintf(fid, '   Sharpe Ratio: %.3f\n', results.statistical.sharpe);
    fprintf(fid, '   Max Drawdown: $%.4f\n\n', results.statistical.max_drawdown);
    
    % Momentum Arbitrage
    fprintf(fid, '2. MOMENTUM ARBITRAGE\n');
    fprintf(fid, '   Trades Executed: %d\n', results.momentum.total_trades);
    fprintf(fid, '   Total Return: $%.4f\n', results.momentum.total_return);
    fprintf(fid, '   Average Return: $%.4f\n', results.momentum.avg_return);
    fprintf(fid, '   Win Rate: %.1f%%\n', results.momentum.win_rate);
    fprintf(fid, '   Sharpe Ratio: %.3f\n', results.momentum.sharpe);
    fprintf(fid, '   Max Drawdown: $%.4f\n\n', results.momentum.max_drawdown);
    
    % Volatility Arbitrage
    fprintf(fid, '3. VOLATILITY-ADJUSTED ARBITRAGE\n');
    fprintf(fid, '   Trades Executed: %d\n', results.volatility.total_trades);
    fprintf(fid, '   Total Return: $%.4f\n', results.volatility.total_return); 
    fprintf(fid, '   Average Return: $%.4f\n', results.volatility.avg_return);
    fprintf(fid, '   Win Rate: %.1f%%\n', results.volatility.win_rate);
    fprintf(fid, '   Sharpe Ratio: %.3f\n', results.volatility.sharpe);
    fprintf(fid, '   Max Drawdown: $%.4f\n\n', results.volatility.max_drawdown);
    
    % Portfolio
    fprintf(fid, '4. OPTIMIZED PORTFOLIO\n');
    fprintf(fid, '   Total Return: $%.4f\n', results.portfolio.total_return);
    fprintf(fid, '   Average Return: $%.4f\n', results.portfolio.avg_return);
    fprintf(fid, '   Win Rate: %.1f%%\n', results.portfolio.win_rate);
    fprintf(fid, '   Sharpe Ratio: %.3f\n', results.portfolio.sharpe);
    fprintf(fid, '   Max Drawdown: $%.4f\n\n', results.portfolio.max_drawdown);
    
    % Current Signals
    fprintf(fid, 'CURRENT MARKET SIGNALS:\n');
    fprintf(fid, '----------------------\n');
    fprintf(fid, 'Statistical Signal: %.0f\n', results.current_signals.statistical);
    fprintf(fid, 'Momentum Signal: %.0f\n', results.current_signals.momentum);
    fprintf(fid, 'Volatility Position: %.3f\n', results.current_signals.volatility_position);
    fprintf(fid, 'RECOMMENDATION: %s\n', results.current_signals.recommendation);
    fprintf(fid, 'Confidence Level: %.1f%%\n\n', results.current_signals.confidence * 100);
    
    fprintf(fid, 'STRATEGY RANKING (by Sharpe Ratio):\n');
    fprintf(fid, '----------------------------------\n');
    
    % Rank strategies
    sharpes = [results.statistical.sharpe, results.momentum.sharpe, ...
               results.volatility.sharpe, results.portfolio.sharpe];
    [sorted_sharpes, idx] = sort(sharpes, 'descend');
    strategy_names = {'Statistical', 'Momentum', 'Volatility', 'Portfolio'};
    
    for i = 1:length(idx)
        fprintf(fid, '%d. %s Strategy (Sharpe: %.3f)\n', i, strategy_names{idx(i)}, sorted_sharpes(i));
    end
    
    fprintf(fid, '\n========================================\n');
    fprintf(fid, 'Analysis Complete - Ready for Deployment\n');
    fprintf(fid, '========================================\n');
    
    fclose(fid);
    fprintf('Comprehensive report saved to: %s\n', report_file);
end
