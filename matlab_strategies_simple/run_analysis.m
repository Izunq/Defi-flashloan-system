
% MATLAB Batch Script for Strategy Analysis
fprintf('Starting MATLAB Strategy Development...\n');

% Add current directory to path
addpath('C:\Users\mahia\New_Flashloan\matlab_strategies_simple');

% Set up data
data_file = 'C:\Users\mahia\New_Flashloan\matlab_strategies_simple\test_data.csv';
output_file = 'C:\Users\mahia\New_Flashloan\matlab_strategies_simple\results\core_strategies_123049.mat';

% Run analysis
fprintf('Running develop_core_strategies...\n');
try
    results = develop_core_strategies(data_file, output_file);
    fprintf('MATLAB Strategy Analysis Completed Successfully!\n');
catch ME
    fprintf('Error in strategy development: %s\n', ME.message);
    rethrow(ME);
end

% Exit MATLAB
exit;
