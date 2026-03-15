% MATLAB Cloud Worker Configuration Script
% Run this in your local MATLAB after setting up the EC2 instance
% Generated: June 15, 2025

fprintf('🚀 Setting up MATLAB Cloud Worker Connection...\n');

% IMPORTANT: Replace these values with your actual EC2 information
EC2_IP = 'YOUR-EC2-INSTANCE-IP';  % Get this from AWS console after setup
KEY_FILE = 'C:\Users\mahia\New_Flashloan\matlab-worker-key.pem';  % Update if different

% Verify inputs
if strcmp(EC2_IP, 'YOUR-EC2-INSTANCE-IP')
    error('❌ Please update EC2_IP with your actual instance IP address');
end

if ~exist(KEY_FILE, 'file')
    error('❌ Key file not found: %s', KEY_FILE);
end

try
    fprintf('🔧 Creating cluster profile...\n');
    
    % Create cluster profile
    c = parcluster('generic');
    
    % Configure connection
    c.Host = EC2_IP;
    c.NumWorkers = 16;  % c5.4xlarge has 16 vCPUs
    c.OperatingSystem = 'unix';
    c.Username = 'ec2-user';
    c.IdentityFile = KEY_FILE;
    c.ClusterMatlabRoot = '/usr/local/MATLAB/R2024b';  % Adjust if different
    
    % Set job storage location
    job_dir = 'C:\temp\matlab_jobs';
    if ~exist(job_dir, 'dir')
        mkdir(job_dir);
    end
    c.JobStorageLocation = job_dir;
    
    % Advanced configuration for better performance
    c.SubmitArguments = '-l walltime=12:00:00 -l nodes=1:ppn=16';
    c.NumThreads = 1;  % Single-threaded workers for better parallel efficiency
    
    % Save profile
    c.saveProfile('CloudWorker');
    
    fprintf('✅ Cloud worker profile created successfully!\n');
    fprintf('   Profile name: CloudWorker\n');
    fprintf('   Host: %s\n', EC2_IP);
    fprintf('   Workers: %d\n', c.NumWorkers);
    fprintf('   Key file: %s\n', KEY_FILE);
    
    % Test connection
    fprintf('🔍 Testing connection...\n');
    
    % Start small pool for testing
    fprintf('   Starting test pool with 2 workers...\n');
    pool = parpool(c, 2);
    
    % Simple test job
    fprintf('   Running parallel test...\n');
    tic;
    result = test_parallel_computation();
    test_time = toc;
    
    fprintf('✅ Connection test successful!\n');
    fprintf('   Test completed in %.2f seconds\n', test_time);
    fprintf('   Result size: %dx%d\n', size(result));
    
    % Clean up test pool
    delete(pool);
    
    % Show usage examples
    fprintf('\n📚 Usage Examples:\n');
    fprintf('   parpool(''CloudWorker'', 16);  %% Start full pool\n');
    fprintf('   parfor i = 1:1000; result(i) = heavy_computation(i); end\n');
    fprintf('   delete(gcp(''nocreate''));  %% Close pool when done\n');
    
    fprintf('\n💡 Pro Tips:\n');
    fprintf('   - Use parfor for embarrassingly parallel loops\n');
    fprintf('   - Use parfeval for asynchronous tasks\n');
    fprintf('   - Monitor costs with AWS console\n');
    fprintf('   - Stop EC2 instance when not in use\n');
    
catch ME
    fprintf('❌ Setup failed: %s\n', ME.message);
    fprintf('🔧 Troubleshooting:\n');
    fprintf('   1. Verify EC2 instance is running\n');
    fprintf('   2. Check security group allows your IP\n');
    fprintf('   3. Ensure MATLAB Parallel Server is installed on EC2\n');
    fprintf('   4. Verify SSH key file path and permissions\n');
    
    % Additional debug info
    fprintf('\nDebug Information:\n');
    fprintf('   MATLAB version: %s\n', version);
    fprintf('   Parallel Computing Toolbox: %s\n', ...
            license('test', 'Distrib_Computing_Toolbox'));
end

function result = test_parallel_computation()
    % Simple parallel test function
    fprintf('      Computing 1000 random matrices in parallel...\n');
    result = zeros(1000, 1);
    parfor i = 1:1000
        % Each worker computes sum of a random 100x100 matrix
        temp_matrix = rand(100, 100);
        result(i) = sum(temp_matrix, 'all');
    end
end

% DeFi-specific test function
function profit_opportunities = test_defi_arbitrage_parallel()
    % Example: Parallel arbitrage opportunity scanning
    % This would be your actual DeFi analysis code
    
    fprintf('      Testing DeFi arbitrage computation...\n');
    
    % Simulate token pairs
    num_pairs = 1000;
    profit_opportunities = zeros(num_pairs, 1);
    
    parfor i = 1:num_pairs
        % Simulate arbitrage calculation for each token pair
        % In real implementation, this would connect to exchanges
        price_diff = rand() * 0.05;  % 0-5% price difference
        if price_diff > 0.02  % 2% threshold
            profit_opportunities(i) = price_diff;
        end
    end
    
    profitable_pairs = sum(profit_opportunities > 0);
    fprintf('      Found %d profitable arbitrage opportunities\n', profitable_pairs);
end
