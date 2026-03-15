% Advanced DeFi Trading Strategy using Simulink
% This demonstrates a complete model-based design approach for arbitrage trading
% Author: DeFi Arbitrage System
% Date: June 17, 2025

function demo_advanced_trading_strategy()
    % Main demonstration function
    
    fprintf('🚀 Advanced DeFi Trading Strategy Demo with Simulink\n');
    fprintf('=' * 60, '\n');
    
    % Create advanced trading strategy model
    create_advanced_strategy_model();
    
    % Run market simulation
    run_market_simulation();
    
    % Analyze results
    analyze_trading_performance();
    
    fprintf('✅ Demo completed successfully!\n');
end

function create_advanced_strategy_model()
    % Create comprehensive trading strategy model
    
    fprintf('📊 Creating Advanced Trading Strategy Model...\n');
    
    model_name = 'Advanced_DeFi_Trading_Strategy';
    
    % Create new model
    new_system(model_name);
    open_system(model_name);
    
    % === INPUT SUBSYSTEM ===
    add_block('simulink/Ports & Subsystems/Subsystem', [model_name '/Market_Data_Input']);
    
    % Market data inputs
    add_block('simulink/Sources/In1', [model_name '/Market_Data_Input/ETH_Price_Uniswap']);
    add_block('simulink/Sources/In1', [model_name '/Market_Data_Input/ETH_Price_Sushiswap']);
    add_block('simulink/Sources/In1', [model_name '/Market_Data_Input/ETH_Price_Balancer']);
    add_block('simulink/Sources/In1', [model_name '/Market_Data_Input/Gas_Price_Gwei']);
    add_block('simulink/Sources/In1', [model_name '/Market_Data_Input/Block_Number']);
    add_block('simulink/Sources/In1', [model_name '/Market_Data_Input/Network_Congestion']);
    
    % Liquidity data
    add_block('simulink/Sources/In1', [model_name '/Market_Data_Input/Uniswap_Liquidity']);
    add_block('simulink/Sources/In1', [model_name '/Market_Data_Input/Sushiswap_Liquidity']);
    add_block('simulink/Sources/In1', [model_name '/Market_Data_Input/Balancer_Liquidity']);
    
    % === SIGNAL PROCESSING SUBSYSTEM ===
    add_block('simulink/Ports & Subsystems/Subsystem', [model_name '/Signal_Processing']);
    
    % Price filtering and smoothing
    add_block('simulink/Discrete/Discrete Filter', [model_name '/Signal_Processing/ETH_Price_Filter']);
    add_block('simulink/Math Operations/Running Average', [model_name '/Signal_Processing/Price_MA_Fast']);
    add_block('simulink/Math Operations/Running Average', [model_name '/Signal_Processing/Price_MA_Slow']);
    
    % Volatility calculation
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/Signal_Processing/Volatility_Calculator']);
    
    % Technical indicators
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/Signal_Processing/RSI_Calculator']);
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/Signal_Processing/MACD_Calculator']);
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/Signal_Processing/Bollinger_Bands']);
    
    % === ARBITRAGE DETECTION SUBSYSTEM ===
    add_block('simulink/Ports & Subsystems/Subsystem', [model_name '/Arbitrage_Detection']);
    
    % Price difference calculations
    add_block('simulink/Math Operations/Subtract', [model_name '/Arbitrage_Detection/Uni_Sushi_Spread']);
    add_block('simulink/Math Operations/Subtract', [model_name '/Arbitrage_Detection/Uni_Balancer_Spread']);
    add_block('simulink/Math Operations/Subtract', [model_name '/Arbitrage_Detection/Sushi_Balancer_Spread']);
    
    % Opportunity scoring
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/Arbitrage_Detection/Opportunity_Scorer']);
    
    % Profitability calculator
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/Arbitrage_Detection/Profit_Calculator']);
    
    % === MEV PROTECTION SUBSYSTEM ===
    add_block('simulink/Ports & Subsystems/Subsystem', [model_name '/MEV_Protection']);
    
    % Front-running detection
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/MEV_Protection/Frontrun_Detector']);
    
    % Private mempool simulation
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/MEV_Protection/Private_Mempool']);
    
    % Gas price optimization
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/MEV_Protection/Gas_Optimizer']);
    
    % === RISK MANAGEMENT SUBSYSTEM ===
    add_block('simulink/Ports & Subsystems/Subsystem', [model_name '/Risk_Management']);
    
    % Portfolio value tracking
    add_block('simulink/Continuous/Integrator', [model_name '/Risk_Management/Portfolio_Integrator']);
    
    % Risk metrics calculation
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/Risk_Management/VaR_Calculator']);
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/Risk_Management/Sharpe_Ratio']);
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/Risk_Management/Drawdown_Monitor']);
    
    % Position sizing with Kelly Criterion
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/Risk_Management/Kelly_Position_Sizer']);
    
    % Emergency stop logic
    add_block('simulink/Logic and Bit Operations/Compare To Constant', [model_name '/Risk_Management/Loss_Limit_Check']);
    add_block('simulink/Logic and Bit Operations/Compare To Constant', [model_name '/Risk_Management/Volatility_Check']);
    add_block('simulink/Logic and Bit Operations/Logical Operator', [model_name '/Risk_Management/Emergency_Stop']);
    
    % === EXECUTION SUBSYSTEM ===
    add_block('simulink/Ports & Subsystems/Subsystem', [model_name '/Trade_Execution']);
    
    % Trade routing optimization
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/Trade_Execution/Route_Optimizer']);
    
    % Slippage estimation
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/Trade_Execution/Slippage_Estimator']);
    
    % Transaction batching
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/Trade_Execution/Batch_Optimizer']);
    
    % === MACHINE LEARNING SUBSYSTEM ===
    add_block('simulink/Ports & Subsystems/Subsystem', [model_name '/ML_Predictions']);
    
    % Price prediction model
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/ML_Predictions/LSTM_Price_Predictor']);
    
    % Market regime detection
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/ML_Predictions/Regime_Detector']);
    
    % Reinforcement learning agent
    add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/ML_Predictions/RL_Agent']);
    
    % === OUTPUT SUBSYSTEM ===
    add_block('simulink/Ports & Subsystems/Subsystem', [model_name '/Trading_Outputs']);
    
    % Trading signals
    add_block('simulink/Sinks/Out1', [model_name '/Trading_Outputs/Trade_Signal']);
    add_block('simulink/Sinks/Out1', [model_name '/Trading_Outputs/Trade_Size']);
    add_block('simulink/Sinks/Out1', [model_name '/Trading_Outputs/Target_Exchange']);
    add_block('simulink/Sinks/Out1', [model_name '/Trading_Outputs/Expected_Profit']);
    add_block('simulink/Sinks/Out1', [model_name '/Trading_Outputs/Risk_Score']);
    add_block('simulink/Sinks/Out1', [model_name '/Trading_Outputs/Confidence_Level']);
    
    % Performance metrics
    add_block('simulink/Sinks/Out1', [model_name '/Trading_Outputs/Portfolio_Value']);
    add_block('simulink/Sinks/Out1', [model_name '/Trading_Outputs/Sharpe_Ratio']);
    add_block('simulink/Sinks/Out1', [model_name '/Trading_Outputs/Max_Drawdown']);
    add_block('simulink/Sinks/Out1', [model_name '/Trading_Outputs/Win_Rate']);
    
    % Configure model parameters
    configure_advanced_model(model_name);
    
    % Save model
    save_system(model_name, [model_name '.slx']);
    close_system(model_name);
    
    fprintf('✅ Advanced trading strategy model created\n');
end

function configure_advanced_model(model_name)
    % Configure advanced model parameters
    
    % Set solver for real-time performance
    set_param(model_name, 'Solver', 'FixedStepDiscrete');
    set_param(model_name, 'FixedStep', '0.01'); % 10ms sample time
    set_param(model_name, 'StopTime', 'inf');
    
    % Configure for code generation
    set_param(model_name, 'SystemTargetFile', 'ert.tlc');
    set_param(model_name, 'OptimizeBlockIOStorage', 'on');
    set_param(model_name, 'LocalBlockOutputs', 'off');
    set_param(model_name, 'BooleanDataType', 'on');
    
    % Set data types for efficiency
    set_param(model_name, 'DefaultParameterBehavior', 'Tunable');
    set_param(model_name, 'DefaultBlockDataType', 'double');
    
    % Configure filters
    filter_num = '[0.0625 0.1250 0.1875 0.2500 0.1875 0.1250 0.0625]'; % Low-pass
    set_param([model_name '/Signal_Processing/ETH_Price_Filter'], 'Numerator', filter_num);
    set_param([model_name '/Signal_Processing/ETH_Price_Filter'], 'Denominator', '[1]');
    
    % Configure moving averages
    set_param([model_name '/Signal_Processing/Price_MA_Fast'], 'WindowLength', '10');
    set_param([model_name '/Signal_Processing/Price_MA_Slow'], 'WindowLength', '50');
    
    % Configure risk limits
    set_param([model_name '/Risk_Management/Loss_Limit_Check'], 'const', '0.02'); % 2% max loss
    set_param([model_name '/Risk_Management/Volatility_Check'], 'const', '0.05'); % 5% max volatility
    set_param([model_name '/Risk_Management/Emergency_Stop'], 'Operator', 'OR');
end

function run_market_simulation()
    % Run comprehensive market simulation
    
    fprintf('📈 Running Market Simulation...\n');
    
    % Generate realistic market data
    simulation_time = 3600; % 1 hour simulation
    dt = 0.01; % 10ms time step
    time_vector = 0:dt:simulation_time;
    n_samples = length(time_vector);
    
    % Base ETH price around $3000
    base_price = 3000;
    
    % Generate correlated price movements for different exchanges
    % Uniswap (most liquid, reference price)
    price_trend = cumsum(randn(n_samples, 1) * 0.001); % Random walk
    eth_price_uni = base_price * (1 + price_trend + 0.02 * sin(time_vector' / 300)); % Slight oscillation
    
    % Sushiswap (slight delay and spread)
    delay_samples = round(0.5 / dt); % 0.5 second delay
    eth_price_sushi = [eth_price_uni(1) * ones(delay_samples, 1); eth_price_uni(1:end-delay_samples)];
    eth_price_sushi = eth_price_sushi .* (1 + randn(n_samples, 1) * 0.0005); % Add noise
    
    % Balancer (different pricing due to weighted pools)
    eth_price_balancer = eth_price_uni .* (1 + randn(n_samples, 1) * 0.001 + 0.001); % Slight premium
    
    % Gas price simulation (varies with network congestion)
    base_gas = 50; % 50 gwei base
    gas_spikes = poissrnd(0.001, n_samples, 1) * 200; % Random gas spikes
    network_congestion = 0.5 + 0.3 * sin(time_vector' / 600) + randn(n_samples, 1) * 0.1; % Cyclical congestion
    gas_price = max(20, base_gas + gas_spikes + network_congestion * 100); % 20 gwei minimum
    
    % Liquidity simulation (decreases during high volatility)
    volatility = movstd(diff(eth_price_uni), 100); % Rolling volatility
    volatility = [volatility(1); volatility]; % Pad for same length
    
    base_liquidity_uni = 50e6; % $50M base liquidity
    liquidity_uni = base_liquidity_uni * (1 - volatility * 10); % Liquidity decreases with volatility
    liquidity_sushi = liquidity_uni * 0.7; % 70% of Uniswap liquidity
    liquidity_balancer = liquidity_uni * 0.4; % 40% of Uniswap liquidity
    
    % Block number (increases linearly)
    block_number = 18000000 + (1:n_samples)'; % Starting from recent block
    
    % Create simulation data structure
    sim_data = struct();
    sim_data.time = time_vector';
    sim_data.eth_price_uni = eth_price_uni;
    sim_data.eth_price_sushi = eth_price_sushi;
    sim_data.eth_price_balancer = eth_price_balancer;
    sim_data.gas_price = gas_price;
    sim_data.liquidity_uni = liquidity_uni;
    sim_data.liquidity_sushi = liquidity_sushi;
    sim_data.liquidity_balancer = liquidity_balancer;
    sim_data.network_congestion = network_congestion;
    sim_data.block_number = block_number;
    
    % Save simulation data
    save('market_simulation_data.mat', 'sim_data');
    
    fprintf('✅ Market simulation data generated\n');
    fprintf('   Duration: %.1f hours\n', simulation_time / 3600);
    fprintf('   Samples: %d\n', n_samples);
    fprintf('   Sample rate: %.0f Hz\n', 1/dt);
end

function analyze_trading_performance()
    % Analyze trading strategy performance
    
    fprintf('📊 Analyzing Trading Performance...\n');
    
    % Load simulation data
    if ~exist('market_simulation_data.mat', 'file')
        fprintf('❌ Simulation data not found. Run simulation first.\n');
        return;
    end
    
    load('market_simulation_data.mat', 'sim_data');
    
    % Calculate arbitrage opportunities
    opportunities = detect_arbitrage_opportunities(sim_data);
    
    % Simulate trading performance
    performance = simulate_trading_performance(sim_data, opportunities);
    
    % Generate performance report
    generate_performance_report(performance);
    
    % Create visualizations
    create_performance_visualizations(sim_data, opportunities, performance);
    
    fprintf('✅ Performance analysis completed\n');
end

function opportunities = detect_arbitrage_opportunities(sim_data)
    % Detect arbitrage opportunities in simulation data
    
    fprintf('🔍 Detecting arbitrage opportunities...\n');
    
    % Calculate price spreads
    uni_sushi_spread = sim_data.eth_price_uni - sim_data.eth_price_sushi;
    uni_balancer_spread = sim_data.eth_price_uni - sim_data.eth_price_balancer;
    sushi_balancer_spread = sim_data.eth_price_sushi - sim_data.eth_price_balancer;
    
    % Calculate percentage spreads
    uni_sushi_pct = uni_sushi_spread ./ sim_data.eth_price_uni * 100;
    uni_balancer_pct = uni_balancer_spread ./ sim_data.eth_price_uni * 100;
    sushi_balancer_pct = sushi_balancer_spread ./ sim_data.eth_price_sushi * 100;
    
    % Define opportunity thresholds (considering gas costs)
    min_profit_threshold = 0.1; % 0.1% minimum profit
    gas_cost_usd = sim_data.gas_price * 200000 * 1e-9 * sim_data.eth_price_uni; % Approx gas cost
    dynamic_threshold = gas_cost_usd ./ (sim_data.eth_price_uni * 100) * 100; % Dynamic threshold based on gas
    
    % Detect opportunities
    opportunities = struct();
    opportunities.time = sim_data.time;
    
    % Uni-Sushi opportunities
    uni_sushi_profitable = abs(uni_sushi_pct) > max(min_profit_threshold, dynamic_threshold);
    opportunities.uni_sushi_signal = uni_sushi_profitable .* sign(uni_sushi_pct);
    opportunities.uni_sushi_profit_pct = uni_sushi_pct;
    
    % Uni-Balancer opportunities
    uni_balancer_profitable = abs(uni_balancer_pct) > max(min_profit_threshold, dynamic_threshold);
    opportunities.uni_balancer_signal = uni_balancer_profitable .* sign(uni_balancer_pct);
    opportunities.uni_balancer_profit_pct = uni_balancer_pct;
    
    % Sushi-Balancer opportunities
    sushi_balancer_profitable = abs(sushi_balancer_pct) > max(min_profit_threshold, dynamic_threshold);
    opportunities.sushi_balancer_signal = sushi_balancer_profitable .* sign(sushi_balancer_pct);
    opportunities.sushi_balancer_profit_pct = sushi_balancer_pct;
    
    % Calculate optimal trade sizes using available liquidity
    opportunities.optimal_trade_size = calculate_optimal_trade_size(sim_data, opportunities);
    
    total_opportunities = sum(uni_sushi_profitable) + sum(uni_balancer_profitable) + sum(sushi_balancer_profitable);
    fprintf('   Found %d total opportunities\n', total_opportunities);
    fprintf('   Uni-Sushi: %d opportunities\n', sum(uni_sushi_profitable));
    fprintf('   Uni-Balancer: %d opportunities\n', sum(uni_balancer_profitable));
    fprintf('   Sushi-Balancer: %d opportunities\n', sum(sushi_balancer_profitable));
end

function optimal_size = calculate_optimal_trade_size(sim_data, opportunities)
    % Calculate optimal trade size considering liquidity and slippage
    
    % Base trade size (1% of available liquidity)
    base_size_factor = 0.01;
    
    % Calculate for each opportunity type
    uni_liquidity = min(sim_data.liquidity_uni, sim_data.liquidity_sushi);
    balancer_liquidity = sim_data.liquidity_balancer;
    
    % Uni-Sushi optimal size
    uni_sushi_size = uni_liquidity * base_size_factor .* abs(opportunities.uni_sushi_signal);
    
    % Uni-Balancer optimal size
    uni_balancer_liquidity = min(sim_data.liquidity_uni, balancer_liquidity);
    uni_balancer_size = uni_balancer_liquidity * base_size_factor .* abs(opportunities.uni_balancer_signal);
    
    % Sushi-Balancer optimal size
    sushi_balancer_liquidity = min(sim_data.liquidity_sushi, balancer_liquidity);
    sushi_balancer_size = sushi_balancer_liquidity * base_size_factor .* abs(opportunities.sushi_balancer_signal);
    
    % Take maximum opportunity
    optimal_size = max([uni_sushi_size, uni_balancer_size, sushi_balancer_size], [], 2);
end

function performance = simulate_trading_performance(sim_data, opportunities)
    % Simulate actual trading performance with realistic constraints
    
    fprintf('💰 Simulating trading performance...\n');
    
    % Initial conditions
    initial_capital = 1000000; % $1M starting capital
    capital = initial_capital;
    gas_cost_per_trade = 200000; % Gas units per arbitrage trade
    
    % Track performance metrics
    n_samples = length(sim_data.time);
    capital_history = zeros(n_samples, 1);
    trades_executed = 0;
    total_gas_cost = 0;
    profits = [];
    trade_times = [];
    
    % Risk management parameters
    max_position_size = initial_capital * 0.1; % Max 10% of capital per trade
    stop_loss_threshold = -0.05; % Stop trading if down 5%
    
    for i = 1:n_samples
        % Current portfolio value
        current_return = (capital - initial_capital) / initial_capital;
        
        % Check stop-loss condition
        if current_return < stop_loss_threshold
            capital_history(i) = capital;
            continue;
        end
        
        % Find best opportunity at current time
        opportunities_at_t = [
            opportunities.uni_sushi_profit_pct(i) * (opportunities.uni_sushi_signal(i) ~= 0),
            opportunities.uni_balancer_profit_pct(i) * (opportunities.uni_balancer_signal(i) ~= 0),
            opportunities.sushi_balancer_profit_pct(i) * (opportunities.sushi_balancer_signal(i) ~= 0)
        ];
        
        [max_profit_pct, best_opportunity] = max(abs(opportunities_at_t));
        
        % Execute trade if profitable
        if max_profit_pct > 0
            % Calculate trade size
            base_trade_size = min(opportunities.optimal_trade_size(i), max_position_size);
            
            % Calculate gas cost
            gas_cost_usd = gas_cost_per_trade * sim_data.gas_price(i) * 1e-9 * sim_data.eth_price_uni(i);
            
            % Calculate net profit
            gross_profit = base_trade_size * max_profit_pct / 100;
            net_profit = gross_profit - gas_cost_usd;
            
            % Execute trade if still profitable after gas
            if net_profit > 0
                capital = capital + net_profit;
                total_gas_cost = total_gas_cost + gas_cost_usd;
                trades_executed = trades_executed + 1;
                profits = [profits; net_profit];
                trade_times = [trade_times; sim_data.time(i)];
            end
        end
        
        capital_history(i) = capital;
    end
    
    % Calculate performance metrics
    final_return = (capital - initial_capital) / initial_capital;
    total_profit = capital - initial_capital;
    
    % Calculate Sharpe ratio (assuming 2% risk-free rate)
    returns = diff(capital_history) ./ capital_history(1:end-1);
    returns = returns(returns ~= 0); % Remove zero returns
    mean_return = mean(returns);
    std_return = std(returns);
    risk_free_rate = 0.02 / (365 * 24 * 3600 / 0.01); % Annualized to sample rate
    sharpe_ratio = (mean_return - risk_free_rate) / std_return * sqrt(length(returns));
    
    % Calculate maximum drawdown
    running_max = cummax(capital_history);
    drawdown = (capital_history - running_max) ./ running_max;
    max_drawdown = min(drawdown);
    
    % Win rate
    winning_trades = sum(profits > 0);
    win_rate = winning_trades / trades_executed;
    
    % Average profit per trade
    avg_profit_per_trade = mean(profits);
    
    % Compile performance results
    performance = struct();
    performance.initial_capital = initial_capital;
    performance.final_capital = capital;
    performance.total_return = final_return;
    performance.total_profit = total_profit;
    performance.sharpe_ratio = sharpe_ratio;
    performance.max_drawdown = max_drawdown;
    performance.trades_executed = trades_executed;
    performance.win_rate = win_rate;
    performance.avg_profit_per_trade = avg_profit_per_trade;
    performance.total_gas_cost = total_gas_cost;
    performance.capital_history = capital_history;
    performance.profits = profits;
    performance.trade_times = trade_times;
    
    fprintf('   Executed %d trades\n', trades_executed);
    fprintf('   Total profit: $%.2f (%.2f%%)\n', total_profit, final_return * 100);
    fprintf('   Sharpe ratio: %.2f\n', sharpe_ratio);
    fprintf('   Win rate: %.1f%%\n', win_rate * 100);
end

function generate_performance_report(performance)
    % Generate comprehensive performance report
    
    fprintf('\n📋 PERFORMANCE REPORT\n');
    fprintf('=' * 50, '\n');
    
    fprintf('💰 Financial Performance:\n');
    fprintf('   Initial Capital:        $%,.0f\n', performance.initial_capital);
    fprintf('   Final Capital:          $%,.0f\n', performance.final_capital);
    fprintf('   Total Profit:           $%,.2f\n', performance.total_profit);
    fprintf('   Total Return:           %.2f%%\n', performance.total_return * 100);
    fprintf('   Average Profit/Trade:   $%.2f\n', performance.avg_profit_per_trade);
    
    fprintf('\n📊 Risk Metrics:\n');
    fprintf('   Sharpe Ratio:           %.2f\n', performance.sharpe_ratio);
    fprintf('   Maximum Drawdown:       %.2f%%\n', performance.max_drawdown * 100);
    fprintf('   Volatility:             %.2f%%\n', std(diff(performance.capital_history)) / mean(performance.capital_history) * 100);
    
    fprintf('\n🎯 Trading Statistics:\n');
    fprintf('   Total Trades:           %d\n', performance.trades_executed);
    fprintf('   Win Rate:               %.1f%%\n', performance.win_rate * 100);
    fprintf('   Total Gas Costs:        $%.2f\n', performance.total_gas_cost);
    fprintf('   Gas Cost/Profit Ratio:  %.1f%%\n', performance.total_gas_cost / performance.total_profit * 100);
    
    % Calculate hourly metrics
    simulation_hours = max(performance.trade_times) / 3600;
    fprintf('\n⏱️  Time-based Metrics:\n');
    fprintf('   Simulation Duration:    %.1f hours\n', simulation_hours);
    fprintf('   Trades per Hour:        %.1f\n', performance.trades_executed / simulation_hours);
    fprintf('   Profit per Hour:        $%.2f\n', performance.total_profit / simulation_hours);
    
    fprintf('\n' + '=' * 50, '\n');
end

function create_performance_visualizations(sim_data, opportunities, performance)
    % Create comprehensive performance visualizations
    
    fprintf('📈 Creating performance visualizations...\n');
    
    % Create figure with subplots
    figure('Position', [100, 100, 1200, 800]);
    
    % Subplot 1: Price movements and spreads
    subplot(2, 3, 1);
    plot(sim_data.time / 3600, sim_data.eth_price_uni, 'b-', 'LineWidth', 1.5);
    hold on;
    plot(sim_data.time / 3600, sim_data.eth_price_sushi, 'r--', 'LineWidth', 1);
    plot(sim_data.time / 3600, sim_data.eth_price_balancer, 'g:', 'LineWidth', 1);
    xlabel('Time (hours)');
    ylabel('ETH Price ($)');
    title('ETH Prices Across Exchanges');
    legend('Uniswap', 'Sushiswap', 'Balancer', 'Location', 'best');
    grid on;
    
    % Subplot 2: Arbitrage opportunities
    subplot(2, 3, 2);
    opportunity_signals = opportunities.uni_sushi_signal + opportunities.uni_balancer_signal + opportunities.sushi_balancer_signal;
    plot(sim_data.time / 3600, opportunity_signals, 'ko', 'MarkerSize', 2);
    xlabel('Time (hours)');
    ylabel('Arbitrage Signal');
    title('Arbitrage Opportunities');
    ylim([-3, 3]);
    grid on;
    
    % Subplot 3: Portfolio value over time
    subplot(2, 3, 3);
    plot(sim_data.time / 3600, performance.capital_history, 'b-', 'LineWidth', 2);
    hold on;
    yline(performance.initial_capital, 'k--', 'Initial Capital');
    xlabel('Time (hours)');
    ylabel('Portfolio Value ($)');
    title('Portfolio Performance');
    grid on;
    
    % Subplot 4: Gas price and network congestion
    subplot(2, 3, 4);
    yyaxis left;
    plot(sim_data.time / 3600, sim_data.gas_price, 'r-', 'LineWidth', 1);
    ylabel('Gas Price (gwei)');
    yyaxis right;
    plot(sim_data.time / 3600, sim_data.network_congestion, 'b--', 'LineWidth', 1);
    ylabel('Network Congestion');
    xlabel('Time (hours)');
    title('Gas Price and Network Congestion');
    grid on;
    
    % Subplot 5: Profit distribution
    subplot(2, 3, 5);
    if ~isempty(performance.profits)
        histogram(performance.profits, 20, 'FaceColor', 'green', 'FaceAlpha', 0.7);
        xlabel('Profit per Trade ($)');
        ylabel('Frequency');
        title('Profit Distribution');
        grid on;
    end
    
    % Subplot 6: Drawdown
    subplot(2, 3, 6);
    running_max = cummax(performance.capital_history);
    drawdown = (performance.capital_history - running_max) ./ running_max * 100;
    area(sim_data.time / 3600, drawdown, 'FaceColor', 'red', 'FaceAlpha', 0.3);
    xlabel('Time (hours)');
    ylabel('Drawdown (%)');
    title('Portfolio Drawdown');
    grid on;
    
    % Adjust layout and save
    sgtitle('DeFi Arbitrage Trading Strategy Performance Analysis', 'FontSize', 16, 'FontWeight', 'bold');
    
    % Save figure
    savefig('trading_performance_analysis.fig');
    print('trading_performance_analysis.png', '-dpng', '-r300');
    
    fprintf('✅ Visualizations saved\n');
end

% Execute demo
if exist('demo_advanced_trading_strategy', 'file') == 2
    demo_advanced_trading_strategy();
end
