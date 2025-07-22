"""
Validation analysis framework for comparing pvlib simulations with Ampere facility data

This module provides comprehensive validation metrics and analysis tools for
comparing simulated PV performance with actual facility data.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ValidationAnalyzer:
    """Validates pvlib simulation results against Ampere facility data"""
    
    def __init__(self, nrel_results_dir: Optional[Path] = None, 
                 ampere_temp_dir: Optional[Path] = None):
        """
        Initialize the validation analyzer
        
        Args:
            nrel_results_dir: Directory containing NREL simulation results
            ampere_temp_dir: Directory containing processed Ampere data
        """
        self.nrel_results_dir = nrel_results_dir or Path(__file__).parent / "results"
        self.ampere_temp_dir = ampere_temp_dir or Path(__file__).parent.parent / "ampere" / "temp"
        
        # Load pvlib_ready.json for facility metadata
        self.facility_metadata = self._load_facility_metadata()
        
    def _load_facility_metadata(self) -> Dict[str, Any]:
        """Load facility metadata from pvlib_ready.json"""
        pvlib_ready_path = self.ampere_temp_dir / "pvlib_ready.json"
        
        if not pvlib_ready_path.exists():
            raise FileNotFoundError(f"pvlib_ready.json not found at {pvlib_ready_path}")
        
        with open(pvlib_ready_path, 'r') as f:
            data = json.load(f)
        
        # Create facility lookup by ID
        facility_lookup = {}
        for facility in data.get('facilities', []):
            facility_lookup[facility['id']] = facility
        
        return facility_lookup
    
    def calculate_annual_energy_from_readings(self, facility_data: Dict[str, Any]) -> float:
        """
        Calculate annual energy from processed readings data
        
        Args:
            facility_data: Processed facility data
            
        Returns:
            Annual energy in kWh
        """
        if not facility_data.get('success', False):
            return 0.0
        
        readings = facility_data.get('readings', {})
        
        # Try to get energy from Energy readings first
        energy_readings = readings.get('Energy', {})
        if energy_readings.get('count', 0) > 0:
            energy_summary = energy_readings.get('summary', {})
            # For cumulative energy meters, use the max value as the annual total
            if 'max' in energy_summary:
                return energy_summary['max']
            elif 'sum' in energy_summary:
                # Only use sum if it's clearly not cumulative data
                # (check if mean is much smaller than sum)
                if energy_summary.get('mean', 0) * energy_summary.get('count', 1) < energy_summary['sum'] * 0.1:
                    return energy_summary['sum']
        
        # Fallback: try to estimate from power readings
        pac_readings = readings.get('Pac', {})
        if pac_readings.get('count', 0) > 0:
            pac_summary = pac_readings.get('summary', {})
            if 'mean' in pac_summary:
                # Estimate annual energy from average power
                # This is a rough approximation
                avg_power_kw = pac_summary['mean']
                hours_per_year = 8760
                return avg_power_kw * hours_per_year
        
        return 0.0
    
    def calculate_capacity_factor(self, annual_energy_kwh: float, facility_id: str) -> float:
        """
        Calculate capacity factor from annual energy
        
        Args:
            annual_energy_kwh: Annual energy in kWh
            facility_id: Facility ID for getting power rating
            
        Returns:
            Capacity factor as percentage
        """
        facility_metadata = self.facility_metadata.get(facility_id, {})
        facility_power_kw = facility_metadata.get('facility_power_kw', 0)
        
        if facility_power_kw > 0:
            hours_per_year = 8760
            max_possible_energy = facility_power_kw * hours_per_year
            return (annual_energy_kwh / max_possible_energy) * 100
        
        return 0.0
    
    def load_simulation_results(self, results_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Load pvlib simulation results
        
        Args:
            results_file: Specific results file to load (optional)
            
        Returns:
            Dictionary with simulation results
        """
        if results_file:
            results_path = self.nrel_results_dir / results_file
        else:
            # Find the most recent results file
            results_files = list(self.nrel_results_dir.glob("simulation_results_*.json"))
            if not results_files:
                raise FileNotFoundError("No simulation results files found")
            
            results_path = max(results_files, key=lambda f: f.stat().st_mtime)
        
        print(f"Loading simulation results from: {results_path}")
        
        with open(results_path, 'r') as f:
            return json.load(f)
    
    def load_ampere_data(self, year: int = 2022) -> Dict[str, Any]:
        """
        Load processed Ampere facility data for a specific year
        
        Args:
            year: Year to load data for
            
        Returns:
            Dictionary with Ampere facility data
        """
        ampere_file = self.ampere_temp_dir / f"processed_facility_data_{year}.json"
        
        if not ampere_file.exists():
            raise FileNotFoundError(f"Processed Ampere data not found: {ampere_file}")
        
        print(f"Loading Ampere data from: {ampere_file}")
        
        with open(ampere_file, 'r') as f:
            return json.load(f)
    
    def match_facilities(self, sim_results: Dict[str, Any], 
                        ampere_data: Dict[str, Any]) -> List[str]:
        """
        Find facilities that exist in both simulation and Ampere datasets
        
        Args:
            sim_results: Simulation results data
            ampere_data: Ampere facility data
            
        Returns:
            List of facility IDs that exist in both datasets
        """
        sim_facilities = set(sim_results.get('facilities', {}).keys())
        ampere_facilities = set(ampere_data.get('facilities', {}).keys())
        
        # Find facilities with successful data in both datasets
        matched_facilities = []
        
        for facility_id in sim_facilities.intersection(ampere_facilities):
            sim_facility = sim_results['facilities'].get(facility_id, {})
            ampere_facility = ampere_data['facilities'].get(facility_id, {})
            
            # Check if both have successful data
            if (sim_facility.get('success', False) and 
                ampere_facility.get('success', False)):
                
                # Calculate annual energy from Ampere data
                annual_energy = self.calculate_annual_energy_from_readings(ampere_facility)
                
                if annual_energy > 0:
                    matched_facilities.append(facility_id)
        
        print(f"Found {len(matched_facilities)} facilities with data in both datasets")
        return matched_facilities
    
    def calculate_validation_metrics(self, actual_values: np.ndarray, 
                                   predicted_values: np.ndarray) -> Dict[str, float]:
        """
        Calculate comprehensive validation metrics
        
        Args:
            actual_values: Actual values from Ampere data
            predicted_values: Predicted values from simulation
            
        Returns:
            Dictionary with validation metrics
        """
        # Remove any NaN or infinite values
        mask = np.isfinite(actual_values) & np.isfinite(predicted_values)
        actual_clean = actual_values[mask]
        predicted_clean = predicted_values[mask]
        
        if len(actual_clean) == 0:
            return {'error': 'No valid data points for comparison'}
        
        # Basic error metrics
        mae = mean_absolute_error(actual_clean, predicted_clean)
        mse = mean_squared_error(actual_clean, predicted_clean)
        rmse = np.sqrt(mse)
        
        # Relative error metrics
        mape = np.mean(np.abs((actual_clean - predicted_clean) / actual_clean)) * 100
        
        # Bias metrics
        mean_bias = np.mean(predicted_clean - actual_clean)
        percent_bias = (mean_bias / np.mean(actual_clean)) * 100
        
        # Correlation metrics
        correlation, p_value = stats.pearsonr(actual_clean, predicted_clean)
        r2 = r2_score(actual_clean, predicted_clean)
        
        # Agreement metrics
        mean_actual = np.mean(actual_clean)
        mean_predicted = np.mean(predicted_clean)
        
        # Normalized metrics
        nrmse = rmse / mean_actual
        nmae = mae / mean_actual
        
        return {
            'n_points': len(actual_clean),
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'mape': mape,
            'mean_bias': mean_bias,
            'percent_bias': percent_bias,
            'correlation': correlation,
            'correlation_p_value': p_value,
            'r2_score': r2,
            'nrmse': nrmse,
            'nmae': nmae,
            'mean_actual': mean_actual,
            'mean_predicted': mean_predicted,
            'ratio_predicted_actual': mean_predicted / mean_actual if mean_actual != 0 else np.nan
        }
    
    def validate_annual_energy(self, sim_results: Dict[str, Any], 
                             ampere_data: Dict[str, Any],
                             matched_facilities: List[str]) -> Dict[str, Any]:
        """
        Validate annual energy production between simulation and actual data
        
        Args:
            sim_results: Simulation results
            ampere_data: Ampere facility data
            matched_facilities: List of facility IDs to validate
            
        Returns:
            Dictionary with validation results
        """
        actual_energy = []
        predicted_energy = []
        facility_comparisons = {}
        
        for facility_id in matched_facilities:
            sim_facility = sim_results['facilities'][facility_id]
            ampere_facility = ampere_data['facilities'][facility_id]
            
            # Extract annual energy values
            actual_kwh = self.calculate_annual_energy_from_readings(ampere_facility)
            predicted_kwh = sim_facility['annual_energy_kwh']
            
            actual_energy.append(actual_kwh)
            predicted_energy.append(predicted_kwh)
            
            # Store individual facility comparison
            facility_comparisons[facility_id] = {
                'facility_name': sim_facility.get('facility_name', 'Unknown'),
                'actual_kwh': actual_kwh,
                'predicted_kwh': predicted_kwh,
                'difference_kwh': predicted_kwh - actual_kwh,
                'percent_difference': ((predicted_kwh - actual_kwh) / actual_kwh) * 100,
                'reference_yield': sim_facility.get('reference_yield'),
                'capacity_factor_actual': self.calculate_capacity_factor(actual_kwh, facility_id),
                'capacity_factor_predicted': sim_facility.get('capacity_factor', 0)
            }
        
        # Calculate validation metrics
        metrics = self.calculate_validation_metrics(
            np.array(actual_energy), 
            np.array(predicted_energy)
        )
        
        return {
            'metric_type': 'annual_energy_kwh',
            'validation_metrics': metrics,
            'facility_comparisons': facility_comparisons,
            'summary': {
                'total_facilities': len(matched_facilities),
                'total_actual_energy': sum(actual_energy),
                'total_predicted_energy': sum(predicted_energy),
                'average_actual_energy': np.mean(actual_energy),
                'average_predicted_energy': np.mean(predicted_energy)
            }
        }
    
    def validate_specific_yield(self, sim_results: Dict[str, Any], 
                              ampere_data: Dict[str, Any],
                              matched_facilities: List[str]) -> Dict[str, Any]:
        """
        Validate specific yield (kWh/kWp) between simulation and actual data
        
        Args:
            sim_results: Simulation results
            ampere_data: Ampere facility data
            matched_facilities: List of facility IDs to validate
            
        Returns:
            Dictionary with validation results
        """
        actual_yield = []
        predicted_yield = []
        facility_comparisons = {}
        
        for facility_id in matched_facilities:
            sim_facility = sim_results['facilities'][facility_id]
            ampere_facility = ampere_data['facilities'][facility_id]
            
            # Calculate specific yield from Ampere data
            actual_energy = self.calculate_annual_energy_from_readings(ampere_facility)
            facility_power = self.facility_metadata[facility_id]['facility_power_kw']
            actual_specific_yield = actual_energy / facility_power if facility_power > 0 else 0
            
            # Get predicted specific yield
            predicted_specific_yield = sim_facility['specific_yield']
            
            actual_yield.append(actual_specific_yield)
            predicted_yield.append(predicted_specific_yield)
            
            # Store individual facility comparison
            facility_comparisons[facility_id] = {
                'facility_name': sim_facility.get('facility_name', 'Unknown'),
                'actual_yield': actual_specific_yield,
                'predicted_yield': predicted_specific_yield,
                'difference_yield': predicted_specific_yield - actual_specific_yield,
                'percent_difference': ((predicted_specific_yield - actual_specific_yield) / actual_specific_yield) * 100 if actual_specific_yield > 0 else 0,
                'facility_power_kw': facility_power,
                'reference_yield': sim_facility.get('reference_yield')
            }
        
        # Calculate validation metrics
        metrics = self.calculate_validation_metrics(
            np.array(actual_yield), 
            np.array(predicted_yield)
        )
        
        return {
            'metric_type': 'specific_yield_kwh_kwp',
            'validation_metrics': metrics,
            'facility_comparisons': facility_comparisons,
            'summary': {
                'total_facilities': len(matched_facilities),
                'average_actual_yield': np.mean(actual_yield),
                'average_predicted_yield': np.mean(predicted_yield)
            }
        }
    
    def generate_validation_report(self, year: int = 2022, 
                                 sim_results_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive validation report
        
        Args:
            year: Year to validate against
            sim_results_file: Specific simulation results file to use
            
        Returns:
            Complete validation report
        """
        print(f"Generating validation report for year {year}...")
        
        # Load data
        sim_results = self.load_simulation_results(sim_results_file)
        ampere_data = self.load_ampere_data(year)
        
        # Match facilities
        matched_facilities = self.match_facilities(sim_results, ampere_data)
        
        if not matched_facilities:
            return {
                'error': 'No matching facilities found between simulation and Ampere data',
                'simulation_facilities': len(sim_results.get('facilities', {})),
                'ampere_facilities': len(ampere_data.get('facilities', {}))
            }
        
        # Perform validations
        energy_validation = self.validate_annual_energy(sim_results, ampere_data, matched_facilities)
        yield_validation = self.validate_specific_yield(sim_results, ampere_data, matched_facilities)
        
        # Generate report
        report = {
            'validation_metadata': {
                'year': year,
                'simulation_file': sim_results_file,
                'total_simulation_facilities': len(sim_results.get('facilities', {})),
                'total_ampere_facilities': len(ampere_data.get('facilities', {})),
                'matched_facilities': len(matched_facilities),
                'validation_timestamp': datetime.now().isoformat()
            },
            'annual_energy_validation': energy_validation,
            'specific_yield_validation': yield_validation,
            'facility_list': matched_facilities
        }
        
        # Save report
        report_filename = f"validation_report_{year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.nrel_results_dir / report_filename
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Validation report saved to: {report_path}")
        
        return report
    
    def create_validation_plots(self, report: Dict[str, Any], 
                              output_dir: Optional[Path] = None) -> None:
        """
        Create visualization plots for validation results, separating outliers
        
        Args:
            report: Validation report
            output_dir: Directory to save plots
        """
        if output_dir is None:
            output_dir = self.nrel_results_dir
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        
        # Annual Energy Validation Plot
        energy_data = report['annual_energy_validation']
        facility_comparisons = energy_data['facility_comparisons']
        
        # Separate facilities by prediction accuracy
        normal_facilities = []
        moderate_outliers = []
        extreme_outliers = []
        
        for comp in facility_comparisons.values():
            percent_diff = abs(comp['percent_difference'])
            
            if percent_diff < 50:
                normal_facilities.append(comp)
            elif percent_diff < 1000:
                moderate_outliers.append(comp)
            else:
                extreme_outliers.append(comp)
        
        # Create comprehensive validation plots
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # 1. Normal facilities - detailed view
        if normal_facilities:
            normal_actual = [comp['actual_kwh'] for comp in normal_facilities]
            normal_predicted = [comp['predicted_kwh'] for comp in normal_facilities]
            
            axes[0, 0].scatter(normal_actual, normal_predicted, alpha=0.7, color='green')
            min_val = min(min(normal_actual), min(normal_predicted))
            max_val = max(max(normal_actual), max(normal_predicted))
            axes[0, 0].plot([min_val, max_val], [min_val, max_val], 'r--', label='1:1 line')
            axes[0, 0].set_xlabel('Actual Energy (kWh)')
            axes[0, 0].set_ylabel('Predicted Energy (kWh)')
            axes[0, 0].set_title(f'Normal Facilities (n={len(normal_facilities)}, <50% error)')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
            
            # Error distribution for normal facilities
            normal_errors = [comp['percent_difference'] for comp in normal_facilities]
            axes[0, 1].hist(normal_errors, bins=15, alpha=0.7, edgecolor='black', color='green')
            axes[0, 1].set_xlabel('Prediction Error (%)')
            axes[0, 1].set_ylabel('Frequency')
            axes[0, 1].set_title('Error Distribution - Normal Facilities')
            axes[0, 1].axvline(0, color='red', linestyle='--', alpha=0.7)
            axes[0, 1].grid(True, alpha=0.3)
        
        # 2. Moderate outliers
        if moderate_outliers:
            mod_actual = [comp['actual_kwh'] for comp in moderate_outliers]
            mod_predicted = [comp['predicted_kwh'] for comp in moderate_outliers]
            
            axes[0, 2].scatter(mod_actual, mod_predicted, alpha=0.7, color='orange')
            axes[0, 2].set_xlabel('Actual Energy (kWh)')
            axes[0, 2].set_ylabel('Predicted Energy (kWh)')
            axes[0, 2].set_title(f'Moderate Outliers (n={len(moderate_outliers)}, 50-1000% error)')
            axes[0, 2].grid(True, alpha=0.3)
            axes[0, 2].set_xscale('log')
            axes[0, 2].set_yscale('log')
        
        # 3. Extreme outliers
        if extreme_outliers:
            ext_actual = [comp['actual_kwh'] for comp in extreme_outliers]
            ext_predicted = [comp['predicted_kwh'] for comp in extreme_outliers]
            
            axes[1, 0].scatter(ext_actual, ext_predicted, alpha=0.7, color='red')
            axes[1, 0].set_xlabel('Actual Energy (kWh)')
            axes[1, 0].set_ylabel('Predicted Energy (kWh)')
            axes[1, 0].set_title(f'Extreme Outliers (n={len(extreme_outliers)}, >1000% error)')
            axes[1, 0].grid(True, alpha=0.3)
            axes[1, 0].set_xscale('log')
            axes[1, 0].set_yscale('log')
        
        # 4. Capacity factor comparison for normal facilities
        if normal_facilities:
            cf_actual = [comp['capacity_factor_actual'] for comp in normal_facilities]
            cf_predicted = [comp['capacity_factor_predicted'] for comp in normal_facilities]
            
            axes[1, 1].scatter(cf_actual, cf_predicted, alpha=0.7, color='blue')
            min_cf = min(min(cf_actual), min(cf_predicted))
            max_cf = max(max(cf_actual), max(cf_predicted))
            axes[1, 1].plot([min_cf, max_cf], [min_cf, max_cf], 'r--', label='1:1 line')
            axes[1, 1].set_xlabel('Actual Capacity Factor (%)')
            axes[1, 1].set_ylabel('Predicted Capacity Factor (%)')
            axes[1, 1].set_title('Capacity Factor Comparison - Normal Facilities')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
        
        # 5. Overall summary
        all_actual = [comp['actual_kwh'] for comp in facility_comparisons.values()]
        all_predicted = [comp['predicted_kwh'] for comp in facility_comparisons.values()]
        
        axes[1, 2].scatter(all_actual, all_predicted, alpha=0.5, color='gray')
        axes[1, 2].set_xlabel('Actual Energy (kWh)')
        axes[1, 2].set_ylabel('Predicted Energy (kWh)')
        axes[1, 2].set_title(f'All Facilities (n={len(facility_comparisons)})')
        axes[1, 2].grid(True, alpha=0.3)
        axes[1, 2].set_xscale('log')
        axes[1, 2].set_yscale('log')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'annual_energy_validation_detailed.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Specific Yield Validation Plot
        yield_data = report['specific_yield_validation']
        yield_comparisons = yield_data['facility_comparisons']
        
        actual_yield = [comp['actual_yield'] for comp in yield_comparisons.values()]
        predicted_yield = [comp['predicted_yield'] for comp in yield_comparisons.values()]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Scatter plot
        ax1.scatter(actual_yield, predicted_yield, alpha=0.6)
        ax1.plot([min(actual_yield), max(actual_yield)], 
                [min(actual_yield), max(actual_yield)], 'r--', label='1:1 line')
        ax1.set_xlabel('Actual Specific Yield (kWh/kWp)')
        ax1.set_ylabel('Predicted Specific Yield (kWh/kWp)')
        ax1.set_title('Specific Yield: Predicted vs Actual')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Error distribution
        yield_errors = [comp['percent_difference'] for comp in yield_comparisons.values()]
        ax2.hist(yield_errors, bins=20, alpha=0.7, edgecolor='black')
        ax2.set_xlabel('Prediction Error (%)')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Distribution of Specific Yield Errors')
        ax2.axvline(0, color='red', linestyle='--', alpha=0.7)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'specific_yield_validation.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Validation plots saved to: {output_dir}")
    
    def print_validation_summary(self, report: Dict[str, Any]) -> None:
        """
        Print a summary of validation results
        
        Args:
            report: Validation report
        """
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        # Handle case where no matching facilities found
        if 'error' in report:
            print(f"Error: {report['error']}")
            if 'simulation_facilities' in report:
                print(f"Simulation facilities: {report['simulation_facilities']}")
            if 'ampere_facilities' in report:
                print(f"Ampere facilities: {report['ampere_facilities']}")
            return
        
        metadata = report['validation_metadata']
        print(f"Year: {metadata['year']}")
        print(f"Matched Facilities: {metadata['matched_facilities']}")
        print(f"Total Simulation Facilities: {metadata['total_simulation_facilities']}")
        print(f"Total Ampere Facilities: {metadata['total_ampere_facilities']}")
        
        print("\nANNUAL ENERGY VALIDATION:")
        print("-" * 30)
        energy_metrics = report['annual_energy_validation']['validation_metrics']
        print(f"  R² Score: {energy_metrics.get('r2_score', 0):.3f}")
        print(f"  RMSE: {energy_metrics.get('rmse', 0):.1f} kWh")
        print(f"  Mean Bias: {energy_metrics.get('percent_bias', 0):.1f}%")
        print(f"  MAPE: {energy_metrics.get('mape', 0):.1f}%")
        print(f"  Correlation: {energy_metrics.get('correlation', 0):.3f}")
        
        print("\nSPECIFIC YIELD VALIDATION:")
        print("-" * 30)
        yield_metrics = report['specific_yield_validation']['validation_metrics']
        print(f"  R² Score: {yield_metrics.get('r2_score', 0):.3f}")
        print(f"  RMSE: {yield_metrics.get('rmse', 0):.1f} kWh/kWp")
        print(f"  Mean Bias: {yield_metrics.get('percent_bias', 0):.1f}%")
        print(f"  MAPE: {yield_metrics.get('mape', 0):.1f}%")
        print(f"  Correlation: {yield_metrics.get('correlation', 0):.3f}")
        
        print("\n" + "="*60)


def main():
    """Main function to run validation analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run validation analysis')
    parser.add_argument('--year', type=int, default=2022, help='Year for validation analysis')
    parser.add_argument('--simulation-results', type=str, help='Path to simulation results file')
    args = parser.parse_args()
    
    try:
        analyzer = ValidationAnalyzer()
        
        # Generate validation report
        report = analyzer.generate_validation_report(year=args.year, sim_results_file=args.simulation_results)
        
        # Print summary
        analyzer.print_validation_summary(report)
        
        # Create plots
        try:
            analyzer.create_validation_plots(report)
        except Exception as e:
            print(f"Warning: Could not create plots: {e}")
        
        print(f"\nValidation analysis completed successfully!")
        
    except Exception as e:
        print(f"Error during validation analysis: {e}")
        raise


if __name__ == "__main__":
    main()