function[A_0,A_opt,r,r_opt,A_ext,A_ext_opt,rough_0,rough_opt,Af0,Af_opt,Vf_0,Vf_opt]=fuselage_optimizer(z_ml, wing_ml, tail_ml, fus_ml, min_ml, max_ml)

%% 1) Read in fixed data
z         = z_ml;                 % stations [n×1]
A_wing    = wing_ml;
A_tail    = tail_ml;
Af0       = fus_ml;               % initial fuselage cross-sections [n×1]
r_min = min_ml;                    % minimum fuselage radii
r_max = max_ml;
n         = numel(z);

%% 2) Compute initial volume and weights
% Integration weights (trapezoidal rule)
dz = diff(z);
w = zeros(n,1);
w(1)       = dz(1)/2;
w(end)     = dz(end)/2;
w(2:end-1) = (dz(1:end-1) + dz(2:end))/2;
Vf_0 = sum(w' .* Af0);   % original volume



A_min    = pi * r_min.^2;        % minimum fuselage area at each station
A_max   = pi * r_max.^2;        % minimum fuselage area at each station


lb = zeros(n,1);             % safe preallocation
lb(:) = A_min(:);  % assign cleanly
ub = zeros(n,1);             % safe preallocation
ub(:) = A_max(:);  % assign cleanly



%% 4) Objective: minimize roughness of total area distribution
total_obj = @(Af) sum((diff(Af + A_wing + A_tail,2)).^2);


%% 7) Setup fmincon options
opts = optimoptions('fmincon', ...
    'Algorithm', 'sqp', ...
    'Display', 'iter', ...
    'MaxIterations', 10000, ...
    'MaxFunctionEvaluations', 1e7, ...
    'OptimalityTolerance', 1e-9, ...
    'StepTolerance', 1e-16);

%% 8) Run optimization
[Af_opt, Rough_opt, exitflag, output] = fmincon(total_obj, Af0, [], [], [], [], lb, ub, [], opts);

%% 9) Post-process and plot
A_0    = Af0 + A_wing + A_tail;
A_opt  = Af_opt + A_wing + A_tail;

Vf_opt = sum(w' .* Af_opt);   % original volume

rough_0 = total_obj(A_0);
rough_opt = Rough_opt;

r        = sqrt(Af0/pi);
r_opt    = sqrt(Af_opt/pi);

%% Skin surface calculations
drdz0    = gradient(r, z);
drdz_opt = gradient(r_opt, z);

integrand0    = 2*pi .* r .* sqrt(1 + drdz0.^2);
integrand_opt = 2*pi .* r_opt .* sqrt(1 + drdz_opt.^2);

A_ext      = trapz(z, integrand0);
A_ext_opt  = trapz(z, integrand_opt);

end
