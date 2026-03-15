% MATLAB Cloud Worker Usage Examples
% How to use your cloud worker in practice
% Generated: June 15, 2025

%% ========================================================================
%% MATLAB CLOUD WORKER: PRACTICAL USAGE GUIDE
%% ========================================================================

fprintf('📚 MATLAB Cloud Worker Usage Examples\n');
fprintf('=====================================\n\n');

%% ONE-TIME SETUP (Already done via matlab_cloud_config.m)
% This creates the 'CloudWorker' profile pointing to your EC2 instance
% You only need to run this once after setting up the EC2 instance

%% ========================================================================
%% DAILY USAGE: SUPER SIMPLE!
%% ========================================================================

%% Example 1: Basic Parallel Loop
fprintf('Example 1: Basic Parallel Loop\n');
fprintf('------------------------------\n');

% Start cloud workers (16 workers on your c5.4xlarge instance)
fprintf('Starting cloud workers...\n');
parpool('CloudWorker', 16);

% Run parallel computation - this automatically runs on the cloud!
fprintf('Running parallel computation on cloud...\n');
tic;
results = zeros(1000, 1);
parfor i = 1:1000  % This runs on your 16 cloud workers
    results(i) = sum(rand(100, 100), 'all');  % Each worker does this
end
computation_time = toc;

fprintf('✅ Completed in %.2f seconds\n', computation_time);
fprintf('💡 This used 16 cloud workers automatically!\n\n');

% Clean up (stops cloud workers, saves costs)
delete(gcp('nocreate'));

%% ========================================================================
%% DEFI-SPECIFIC EXAMPLES
%% ========================================================================

%% Example 2: Multi-Exchange Arbitrage Scanning
fprintf('Example 2: DeFi Arbitrage Scanning\n');
fprintf('-----------------------------------\n');

% Define your token pairs and exchanges
token_pairs = {'ETH-USDC', 'BTC-USDT', 'LINK-ETH', 'UNI-USDC'};  % etc.
exchanges = {'Uniswap', 'SushiSwap', 'Balancer', 'Curve'};
num_pairs = 1000;  % In reality, you'd have many more

% Start workers
parpool('CloudWorker', 16);

% Parallel arbitrage scanning
fprintf('Scanning %d token pairs across %d exchanges...\n', num_pairs, length(exchanges));
tic;
arbitrage_opportunities = zeros(num_pairs, length(exchanges));

parfor pair_idx = 1:num_pairs  % Each worker handles different pairs
    for exchange_idx = 1:length(exchanges)
        % This is where you'd call your actual arbitrage analysis
        % For demo, we'll simulate the computation
        price_difference = analyze_arbitrage_opportunity(pair_idx, exchange_idx);
        arbitrage_opportunities(pair_idx, exchange_idx) = price_difference;
    end
end
scan_time = toc;

% Find profitable opportunities
profitable_threshold = 0.02;  % 2% profit threshold
profitable_count = sum(arbitrage_opportunities > profitable_threshold, 'all');

fprintf('✅ Scan completed in %.2f seconds\n', scan_time);
fprintf('💰 Found %d profitable opportunities\n', profitable_count);

% Visualize results (this runs locally on your laptop)
figure;
heatmap(arbitrage_opportunities);
title('Arbitrage Opportunities Across Exchanges');
xlabel('Exchanges');
ylabel('Token Pairs');

delete(gcp('nocreate'));

%% Example 3: Monte Carlo Portfolio Simulation
fprintf('\nExample 3: Monte Carlo Portfolio Simulation\n');
fprintf('-------------------------------------------\n');

% Portfolio parameters
num_simulations = 100000;  % This would take forever on a laptop!
portfolio_assets = 10;
simulation_days = 365;

parpool('CloudWorker', 16);

fprintf('Running %d Monte Carlo simulations...\n', num_simulations);
tic;
portfolio_values = zeros(num_simulations, 1);

parfor sim = 1:num_simulations  % Perfect for parallel processing
    % Simulate one portfolio path
    portfolio_values(sim) = simulate_portfolio_performance(portfolio_assets, simulation_days);
end
simulation_time = toc;

% Calculate risk metrics (locally)
value_at_risk_95 = prctile(portfolio_values, 5);
expected_return = mean(portfolio_values);
volatility = std(portfolio_values);

fprintf('✅ Simulation completed in %.2f seconds\n', simulation_time);
fprintf('📊 Expected Return: $%.2f\n', expected_return);
fprintf('📊 95%% VaR: $%.2f\n', value_at_risk_95);
fprintf('📊 Volatility: $%.2f\n', volatility);

% Plot results locally
figure;
histogram(portfolio_values, 50);
title('Portfolio Value Distribution (100,000 simulations)');
xlabel('Portfolio Value ($)');
ylabel('Frequency');

delete(gcp('nocreate'));

%% ========================================================================
%% WHAT RUNS WHERE?
%% ========================================================================

fprintf('\n🤔 What Runs Where?\n');
fprintf('===================\n');
fprintf('LOCAL (Your Laptop):\n');
fprintf('  ✅ MATLAB interface and commands\n');
fprintf('  ✅ Plotting and visualization\n');
fprintf('  ✅ Data preparation and results processing\n');
fprintf('  ✅ Interactive development and debugging\n\n');

fprintf('CLOUD (Your EC2 Worker):\n');
fprintf('  ⚡ parfor loop iterations\n');
fprintf('  ⚡ parfeval function calls\n');
fprintf('  ⚡ Heavy mathematical computations\n');
fprintf('  ⚡ Memory-intensive operations\n\n');

%% ========================================================================
%% SMART USAGE PATTERNS
%% ========================================================================

fprintf('💡 Smart Usage Patterns:\n');
fprintf('========================\n');

% Pattern 1: Development vs Production
fprintf('\n1. DEVELOPMENT MODE (Start small):\n');
% parpool('CloudWorker', 2);    % Use fewer workers for testing
% Small dataset for debugging
% delete(gcp('nocreate'));

fprintf('2. PRODUCTION MODE (Scale up):\n');
% parpool('CloudWorker', 16);   % Use all workers for real work
% Full dataset processing
% delete(gcp('nocreate'));

% Pattern 2: Batch Processing
fprintf('\n3. BATCH PROCESSING:\n');
% Start workers once
% Run multiple analyses
% Clean up at the end

% Pattern 3: Cost Management
fprintf('\n4. COST MANAGEMENT:\n');
fprintf('   - Always delete(gcp(''nocreate'')) when done\n');
fprintf('   - Use python monitor_matlab_worker.py status\n');
fprintf('   - Stop EC2 instance when not working\n');

%% ========================================================================
%% HELPER FUNCTIONS (You would implement these)
%% ========================================================================

function profit = analyze_arbitrage_opportunity(pair_idx, exchange_idx)
    % Simulate arbitrage analysis
    % In reality, this would:
    % 1. Fetch prices from exchanges
    % 2. Calculate transaction costs
    % 3. Determine profit potential
    
    % Simulated calculation
    base_profit = rand() * 0.05;  % 0-5% potential profit
    transaction_cost = 0.003;     % 0.3% transaction cost
    profit = max(0, base_profit - transaction_cost);
end

function final_value = simulate_portfolio_performance(num_assets, days)
    % Simulate portfolio performance over time
    % In reality, this would use actual market data and models
    
    initial_value = 10000;  % $10,000 initial portfolio
    daily_returns = randn(days, num_assets) * 0.02;  % 2% daily volatility
    weights = ones(1, num_assets) / num_assets;  % Equal weights
    
    portfolio_value = initial_value;
    for day = 1:days
        day_return = sum(weights .* daily_returns(day, :));
        portfolio_value = portfolio_value * (1 + day_return);
    end
    
    final_value = portfolio_value;
end

%% ========================================================================
%% TROUBLESHOOTING
%% ========================================================================

fprintf('\n🔧 Troubleshooting Tips:\n');
fprintf('=======================\n');
fprintf('❌ "Cannot connect to cluster":\n');
fprintf('   - Check EC2 instance is running\n');
fprintf('   - Verify IP address in cluster profile\n');
fprintf('   - Check security group settings\n\n');

fprintf('❌ "Workers not starting":\n');
fprintf('   - Check MATLAB Parallel Server on EC2\n');
fprintf('   - Verify SSH key permissions\n');
fprintf('   - Try fewer workers initially\n\n');

fprintf('💰 "Costs too high":\n');
fprintf('   - Always delete(gcp(''nocreate'')) after use\n');
fprintf('   - Stop EC2 instance when done\n');
fprintf('   - Use spot instances for production\n\n');

fprintf('🎉 Ready to use your cloud workers!\n');
fprintf('Just remember: parpool → work → delete(gcp)\n');
