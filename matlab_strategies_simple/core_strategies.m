
function results = develop_core_strategies(data_file, output_file)
    try
        fprintf('Starting MATLAB Strategy Development...\n');
        
        % Load data
        data = readtable(data_file);
        results = struct();
        results.timestamp = datestr(now);
        
        % Strategy 1: Mean Reversion
        fprintf('Developing Mean Reversion Strategy...\n');
        spreads = data.price_spread;
        window = 20;
        rolling_mean = movmean(spreads, window);
        rolling_std = movstd(spreads, window);
        z_scores = (spreads - rolling_mean) ./ rolling_std;
        
        % Mean reversion signals
        mr_signals = zeros(size(z_scores));
        mr_signals(z_scores > 2) = -1;  % Sell overpriced
        mr_signals(z_scores < -2) = 1;  % Buy underpriced
        
        % Calculate returns
        mr_positions = generate_positions(mr_signals);
        mr_returns = mr_positions .* data.profit;
        
        results.mean_reversion = struct();
        results.mean_reversion.total_return = sum(mr_returns);
        results.mean_reversion.sharpe_ratio = mean(mr_returns) / std(mr_returns) * sqrt(252);
        results.mean_reversion.win_rate = mean(mr_returns > 0);
        results.mean_reversion.max_drawdown = calculate_max_drawdown(cumsum(mr_returns));
        
        % Strategy 2: Momentum
        fprintf('Developing Momentum Strategy...\n');
        short_ma = movmean(spreads, 5);
        long_ma = movmean(spreads, 20);
        momentum = short_ma - long_ma;
        
        % Momentum signals
        mom_signals = zeros(size(momentum));
        mom_threshold = std(momentum) * 1.5;
        mom_signals(momentum > mom_threshold) = 1;
        mom_signals(momentum < -mom_threshold) = -1;
        
        mom_positions = generate_positions(mom_signals);
        mom_returns = mom_positions .* data.profit;
        
        results.momentum = struct();
        results.momentum.total_return = sum(mom_returns);
        results.momentum.sharpe_ratio = mean(mom_returns) / std(mom_returns) * sqrt(252);
        results.momentum.win_rate = mean(mom_returns > 0);
        results.momentum.max_drawdown = calculate_max_drawdown(cumsum(mom_returns));
        
        % Strategy 3: Volatility Strategy
        fprintf('Developing Volatility Strategy...\n');
        volatility = data.volatility;
        vol_ma = movmean(volatility, 20);
        vol_std = movstd(volatility, 20);
        
        vol_signals = zeros(size(volatility));
        vol_signals(volatility > vol_ma + 2*vol_std) = 1;  % High vol
        vol_signals(volatility < vol_ma - 2*vol_std) = -1; % Low vol
        
        vol_positions = generate_positions(vol_signals);
        vol_returns = vol_positions .* data.profit;
        
        results.volatility = struct();
        results.volatility.total_return = sum(vol_returns);
        results.volatility.sharpe_ratio = mean(vol_returns) / std(vol_returns) * sqrt(252);
        results.volatility.win_rate = mean(vol_returns > 0);
        results.volatility.max_drawdown = calculate_max_drawdown(cumsum(vol_returns));
        
        % Strategy Comparison
        strategies = {'mean_reversion', 'momentum', 'volatility'};
        sharpe_ratios = [results.mean_reversion.sharpe_ratio, ...
                        results.momentum.sharpe_ratio, ...
                        results.volatility.sharpe_ratio];
        
        [~, best_idx] = max(sharpe_ratios);
        results.best_strategy = strategies{best_idx};
        results.best_sharpe = sharpe_ratios(best_idx);
        
        % Portfolio Optimization - Equal Weight
        all_returns = [mr_returns, mom_returns, vol_returns];
        portfolio_returns = mean(all_returns, 2);
        
        results.portfolio = struct();
        results.portfolio.total_return = sum(portfolio_returns);
        results.portfolio.sharpe_ratio = mean(portfolio_returns) / std(portfolio_returns) * sqrt(252);
        results.portfolio.win_rate = mean(portfolio_returns > 0);
        
        % Current Signals
        results.current_signals = struct();
        results.current_signals.mean_reversion = mr_signals(end);
        results.current_signals.momentum = mom_signals(end);
        results.current_signals.volatility = vol_signals(end);
        
        % Overall recommendation
        signal_sum = mr_signals(end) + mom_signals(end) + vol_signals(end);
        if signal_sum >= 2
            results.current_signals.recommendation = 'STRONG_BUY';
        elseif signal_sum == 1
            results.current_signals.recommendation = 'BUY';
        elseif signal_sum == -1
            results.current_signals.recommendation = 'SELL';
        elseif signal_sum <= -2
            results.current_signals.recommendation = 'STRONG_SELL';
        else
            results.current_signals.recommendation = 'HOLD';
        end
        
        % Save results
        save(output_file, 'results');
        
        % Create simple report
        report_file = strrep(output_file, '.mat', '_report.txt');
        create_simple_report(results, report_file);
        
        fprintf('MATLAB Strategy Development Complete!\n');
        fprintf('Best Strategy: %s (Sharpe: %.3f)\n', results.best_strategy, results.best_sharpe);
        fprintf('Current Recommendation: %s\n', results.current_signals.recommendation);
        
    catch ME
        fprintf('MATLAB Error: %s\n', ME.message);
        results = struct('error', ME.message);
    end
end

function positions = generate_positions(signals)
    positions = zeros(size(signals));
    current_pos = 0;
    for i = 1:length(signals)
        if signals(i) ~= 0
            current_pos = signals(i);
        end
        positions(i) = current_pos;
    end
end

function max_dd = calculate_max_drawdown(cumulative_returns)
    running_max = cummax(cumulative_returns);
    drawdowns = cumulative_returns - running_max;
    max_dd = min(drawdowns);
end

function create_simple_report(results, filename)
    fid = fopen(filename, 'w');
    
    fprintf(fid, 'MATLAB ARBITRAGE STRATEGY REPORT\n');
    fprintf(fid, '================================\n');
    fprintf(fid, 'Generated: %s\n\n', results.timestamp);
    
    fprintf(fid, 'STRATEGY PERFORMANCE:\n');
    fprintf(fid, '--------------------\n');
    
    fprintf(fid, 'Mean Reversion Strategy:\n');
    fprintf(fid, '  Total Return: %.4f\n', results.mean_reversion.total_return);
    fprintf(fid, '  Sharpe Ratio: %.3f\n', results.mean_reversion.sharpe_ratio);
    fprintf(fid, '  Win Rate: %.2f%%\n', results.mean_reversion.win_rate * 100);
    fprintf(fid, '  Max Drawdown: %.4f\n\n', results.mean_reversion.max_drawdown);
    
    fprintf(fid, 'Momentum Strategy:\n');
    fprintf(fid, '  Total Return: %.4f\n', results.momentum.total_return);
    fprintf(fid, '  Sharpe Ratio: %.3f\n', results.momentum.sharpe_ratio);
    fprintf(fid, '  Win Rate: %.2f%%\n', results.momentum.win_rate * 100);
    fprintf(fid, '  Max Drawdown: %.4f\n\n', results.momentum.max_drawdown);
    
    fprintf(fid, 'Volatility Strategy:\n');
    fprintf(fid, '  Total Return: %.4f\n', results.volatility.total_return);
    fprintf(fid, '  Sharpe Ratio: %.3f\n', results.volatility.sharpe_ratio);
    fprintf(fid, '  Win Rate: %.2f%%\n', results.volatility.win_rate * 100);
    fprintf(fid, '  Max Drawdown: %.4f\n\n', results.volatility.max_drawdown);
    
    fprintf(fid, 'BEST STRATEGY: %s\n', results.best_strategy);
    fprintf(fid, 'BEST SHARPE RATIO: %.3f\n\n', results.best_sharpe);
    
    fprintf(fid, 'PORTFOLIO PERFORMANCE:\n');
    fprintf(fid, '  Total Return: %.4f\n', results.portfolio.total_return);
    fprintf(fid, '  Sharpe Ratio: %.3f\n', results.portfolio.sharpe_ratio);
    fprintf(fid, '  Win Rate: %.2f%%\n\n', results.portfolio.win_rate * 100);
    
    fprintf(fid, 'CURRENT SIGNALS:\n');
    fprintf(fid, '  Mean Reversion: %d\n', results.current_signals.mean_reversion);
    fprintf(fid, '  Momentum: %d\n', results.current_signals.momentum);
    fprintf(fid, '  Volatility: %d\n', results.current_signals.volatility);
    fprintf(fid, '  RECOMMENDATION: %s\n\n', results.current_signals.recommendation);
    
    fclose(fid);
end
