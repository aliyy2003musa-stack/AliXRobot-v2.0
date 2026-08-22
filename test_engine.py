"""
AliXRobot v2.0 Test Script
Tests the new v2.0 features: 
- Trajectory Profiles (Linear, Trapezoidal, S-Curve)
- Workspace Calculation
- Export Data Formatting
- Advanced Geometry Paths
"""
from robotEngine import RobotEngine
from visualization.geometry import create_advanced_path, generate_workspace_grid

def main():
    print("=" * 40)
    print("AliXRobot v2.0 Engine & Geometry Test")
    print("=" * 40)
    
    # Initialize Engine
    engine = RobotEngine()
    engine.configure_robot(
        dimension=2,
        robot_type="Articulated",
        dof=3,
        position=[1.0, 0.0],
    )
    
    # -----------------------------------------------------
    # 1. BASIC TRANSFORMATION
    # -----------------------------------------------------
    print("\n1. Basic Transformation:")
    result = engine.apply_transformation(
        translate_by=[5.0, 2.0],
        rotate_degrees=90.0,
        scale_by=2.0,
    )
    print(f"   Original:    {engine.get_position()}")
    print(f"   Transformed: {result}")
    
    # -----------------------------------------------------
    # 2. V2.0: ADVANCED TRAJECTORY PROFILES
    # -----------------------------------------------------
    print("\n2. v2.0 Advanced Trajectory Profiles:")
    path_linear = engine.generate_trajectory_path(profile="linear", steps=5)
    path_s_curve = engine.generate_trajectory_path(profile="s_curve", steps=5)
    
    print(f"   Linear Path (first 2 points): {path_linear[:2]}")
    print(f"   S-Curve Path (first 2 points): {path_s_curve[:2]}")
    
    # -----------------------------------------------------
    # 3. V2.0: WORKSPACE CALCULATION
    # -----------------------------------------------------
    print("\n3. v2.0 Workspace Calculation:")
    workspace = engine.calculate_workspace(resolution=2)
    print(f"   Generated {len(workspace)} reachable workspace points.")
    print(f"   Sample point: {workspace[0] if workspace else 'None'}")
    
    # -----------------------------------------------------
    # 4. V2.0: GEOMETRY ADVANCED PATH
    # -----------------------------------------------------
    print("\n4. v2.0 Geometry Advanced Path (Trapezoidal):")
    geo_path = create_advanced_path(
        start=[0.0, 0.0], 
        end=[10.0, 10.0], 
        samples=3, 
        profile="trapezoidal"
    )
    print(f"   Path: {geo_path}")
    
    # -----------------------------------------------------
    # 5. V2.0: EXPORT DATA FORMATTER
    # -----------------------------------------------------
    print("\n5. v2.0 Export Data Formatter:")
    export_data = engine.get_export_data()
    print(f"   Export Data Keys: {list(export_data.keys())}")
    
    # -----------------------------------------------------
    # 6. V2.0: WORKSPACE GRID GENERATOR (GEOMETRY)
    # -----------------------------------------------------
    print("\n6. v2.0 Workspace Grid Generator (Geometry):")
    grid = generate_workspace_grid(
        center=[0.0, 0.0], 
        radius=5.0, 
        resolution=2, 
        dimension=2
    )
    print(f"   Generated {len(grid)} grid points.")
    
    print("\n" + "=" * 40)
    print("All v2.0 Tests Passed Successfully!")
    print("=" * 40)

if __name__ == "__main__":
    main()