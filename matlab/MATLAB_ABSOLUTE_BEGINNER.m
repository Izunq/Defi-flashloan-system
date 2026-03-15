% MATLAB_ABSOLUTE_BEGINNER.m
% For people who have NEVER used MATLAB before
% Just follow the comments step by step!

%% ====================================================================
%% BEFORE YOU START: WHAT TO DO FIRST
%% ====================================================================

% 1. Make sure you ran this in PowerShell first:
%    cd "C:\Users\mahia\New_Flashloan"
%    bash aws_setup_commands.sh
%
% 2. Write down the IP address that command gives you
%
% 3. Now come back to this script

%% ====================================================================
%% UPDATE THIS LINE WITH YOUR IP ADDRESS
%% ====================================================================

% CHANGE the IP address below to match what you got from AWS:
YOUR_EC2_IP = '12.34.56.78';  % <-- CHANGE THIS TO YOUR ACTUAL IP

% Example: if AWS gave you 3.45.67.89, then write:
% YOUR_EC2_IP = '3.45.67.89';

%% ====================================================================
%% AUTOMATIC SETUP (Don't change anything below)
%% ====================================================================

fprintf('🚀 Setting up MATLAB Cloud Computing...\n\n');

% Check if you updated the IP
if strcmp(YOUR_EC2_IP, '12.34.56.78')
    fprintf('❌ STOP! You need to change YOUR_EC2_IP above to your real IP\n');
    fprintf('💡 Look for the IP address that aws_setup_commands.sh gave you\n');
    return;
end

% Set up the cloud connection
try
    c = parcluster('generic');
    c.Host = YOUR_EC2_IP;
    c.NumWorkers = 16;
    c.OperatingSystem = 'unix';
    c.Username = 'ec2-user';
    c.IdentityFile = 'C:\Users\mahia\New_Flashloan\matlab-worker-key.pem';
    
    % Create job folder
    if ~exist('C:\temp\matlab_jobs', 'dir')
        mkdir('C:\temp\matlab_jobs');
    end
    c.JobStorageLocation = 'C:\temp\matlab_jobs';
    
    % Save it
    c.saveProfile('CloudWorker');
    
    fprintf('✅ Cloud worker setup complete!\n');
    fprintf('🎯 Your cloud computer IP: %s\n\n', YOUR_EC2_IP);
    
catch
    fprintf('❌ Setup failed. Check:\n');
    fprintf('  - Did you run aws_setup_commands.sh first?\n');
    fprintf('  - Is your IP address correct?\n');
    fprintf('  - Is your internet working?\n');
    return;
end

%% ====================================================================
%% TEST YOUR CLOUD COMPUTER
%% ====================================================================

fprintf('🧪 Testing your cloud computer...\n');

try
    % Start 2 cloud workers for testing
    parpool('CloudWorker', 2);
    
    % Do a simple test
    test_numbers = 1:100;
    test_results = zeros(size(test_numbers));
    
    parfor i = 1:length(test_numbers)
        test_results(i) = test_numbers(i) * 2;  % Multiply by 2
    end
    
    fprintf('✅ SUCCESS! Your cloud computer is working!\n');
    fprintf('   Test: 1*2=%d, 2*2=%d, 3*2=%d\n', test_results(1), test_results(2), test_results(3));
    
    % Stop the workers
    delete(gcp('nocreate'));
    fprintf('💰 Test complete, workers stopped.\n\n');
    
    % Show what to do next
    fprintf('🎉 CONGRATULATIONS! Everything is working!\n\n');
    
    fprintf('📚 WHAT TO DO NEXT:\n');
    fprintf('==================\n');
    fprintf('Copy and paste any of these examples:\n\n');
    
    % Show Example 1
    fprintf('EXAMPLE 1 - Copy everything between the lines:\n');
    fprintf('----------------------------------------------\n');
    fprintf('parpool(''CloudWorker'', 8);\n');
    fprintf('numbers = 1:1000;\n');
    fprintf('squares = zeros(size(numbers));\n');
    fprintf('parfor i = 1:length(numbers)\n');
    fprintf('    squares(i) = numbers(i)^2;\n');
    fprintf('end\n');
    fprintf('fprintf(''First 10 squares: %%s\\n'', mat2str(squares(1:10)));\n');
    fprintf('delete(gcp(''nocreate''));\n');
    fprintf('----------------------------------------------\n\n');
    
    fprintf('💡 HOW TO USE:\n');
    fprintf('1. Copy the lines between the dashes\n');
    fprintf('2. Paste them into this MATLAB window\n');
    fprintf('3. Press ENTER\n');
    fprintf('4. Watch your cloud computer work!\n\n');
    
    fprintf('🎯 YOU''RE READY TO USE CLOUD COMPUTING!\n');
    
catch
    fprintf('❌ Test failed. Your cloud might not be ready yet.\n');
    fprintf('💡 Wait 2-3 minutes and try running this script again.\n');
end

%% ====================================================================
%% READY-TO-USE EXAMPLES (Copy these after setup works)
%% ====================================================================

% Don't run these automatically - they're for you to copy/paste later

% EXAMPLE 1: Simple Math
% parpool('CloudWorker', 8);
% numbers = 1:1000;
% squares = zeros(size(numbers));
% fprintf('Computing squares on cloud...\n');
% tic;
% parfor i = 1:length(numbers)
%     squares(i) = numbers(i)^2;
% end
% time_taken = toc;
% fprintf('Done in %.2f seconds!\n', time_taken);
% fprintf('First 10 squares: %s\n', mat2str(squares(1:10)));
% delete(gcp('nocreate'));

% EXAMPLE 2: Fake Trading
% parpool('CloudWorker', 16);
% num_trades = 10000;
% profits = zeros(num_trades, 1);
% fprintf('Simulating %d trades...\n', num_trades);
% tic;
% parfor trade = 1:num_trades
%     random_profit = randn() * 100;  % Random profit/loss
%     profits(trade) = random_profit;
% end
% time_taken = toc;
% total_profit = sum(profits);
% fprintf('Trading simulation done in %.2f seconds!\n', time_taken);
% fprintf('Total profit: $%.2f\n', total_profit);
% fprintf('Best trade: $%.2f\n', max(profits));
% fprintf('Worst trade: $%.2f\n', min(profits));
% delete(gcp('nocreate'));

% EXAMPLE 3: Crypto Analysis
% crypto_names = {'Bitcoin', 'Ethereum', 'Dogecoin'};
% parpool('CloudWorker', 8);
% volatilities = zeros(length(crypto_names), 1);
% fprintf('Analyzing cryptocurrencies...\n');
% tic;
% parfor i = 1:length(crypto_names)
%     fake_prices = randn(365, 1) * 50 + 1000;  % Fake daily prices
%     volatilities(i) = std(fake_prices);
% end
% time_taken = toc;
% fprintf('Analysis done in %.2f seconds!\n', time_taken);
% for i = 1:length(crypto_names)
%     fprintf('%s volatility: $%.2f\n', crypto_names{i}, volatilities(i));
% end
% figure;
% bar(volatilities);
% set(gca, 'XTickLabel', crypto_names);
% title('Crypto Volatility Analysis');
% delete(gcp('nocreate'));
