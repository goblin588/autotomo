"""
Plotting functions for Setup characterisations (+ saving data)
"""

import datetime
import os 
import matplotlib.pyplot as plt
import Libraries.CharModellingLib as cml
import numpy as np
import csv 
from Libraries.BasisVectors import basis_vectors

def createDir(directory_name):
    # directory_name = directory_name + f'_{graph_title}'
    try:
        os.makedirs(directory_name, exist_ok=True)
        assert os.path.exists(directory_name), print(f"Failed creating dir '{directory_name}'.")
        print(f"Directory '{directory_name}' created successfully.")
    except FileExistsError:
        print(f"Directory '{directory_name}' already exists.")
        return 1
    except PermissionError:
        print(f"Permission denied: Unable to create '{directory_name}'.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return 1

def savePlot(fig, graph_title, filepath=os.getcwd()):
    # Save plot and data in a folder with todays date and time
    if createDir(filepath):
        filename = graph_title
        fig.savefig(filepath +'/' + filename + '_FIGURE.png')

def saveData(data, normalised_data, angles, graph_title, plot_type = None, filepath=os.getcwd()):
    if createDir(filepath):
        filename = graph_title
        writeData2File(filepath +'/'+ filename + '_DATA', data=data, normalised_data=normalised_data, angles=angles, plot_type=plot_type)

def write2file(filename, data, normalised_data, angles): 
    # Create a file with DATE, ANGS, RAW and NORM Data
    with open(f"{filename}.csv", 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow({f'DATE: {datetime.datetime.now().strftime("%Y/%m/%d @ %H:%M:%S")}'})
        writer.writerow({f'ANGLES: {angles}'})
        writer.writerow({f'RAW_DATA: {data}'})
        writer.writerow({f'NORM_DATA: {normalised_data}'})

def writeData2File(filename, data, normalised_data, angles, plot_type): 
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    # Create a file with DATE, ANGS, RAW and NORM Data
    with open(f"{filename}.csv", 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if plot_type is not None:
            writer.writerow([f'PLOT TYPE: {plot_type}'])
        writer.writerow([f'DATE: {datetime.datetime.now().strftime("%Y/%m/%d @ %H:%M:%S")}'])
        writer.writerow([f'ANGLES: {angles}'])

        if '0' in data.keys() or 0 in data.keys():
            for key in data:
                writer.writerow([f'RAW DATA [{key}]: {data[key]}'])
        else: writer.writerow([f'RAW_DATA: {data}'])

        if '0' in normalised_data.keys() or 0 in normalised_data.keys():
            for key in normalised_data:
                writer.writerow([f'NORM_DATA[{key}]: {normalised_data[key]}'])
        else: writer.writerow([f'NORM_DATA: {normalised_data}'])

def plot_n_chars(searchMatrix, data, base_title, n, SAVE=False):
    for i in range(n):
        graph_title = f'FIG_{n}_' + base_title
        plot_characterisation(searchMatrix, data, graph_title, showPlot=False)

def plot_characterisation(data, graph_title, angles, plot_type = None, 
                          note = None, save_plot=True, save_data=True, show_plot=True):
    fit = 0
    multi=False
    measurement_basis = basis_vectors
    normalized_data = cml.normalise_full_tomo_data(data)
    searchMatrix = cml.getUnitary(q1=angles['q1'], h1=angles['h1'], q12=angles['q12'], 
                                    h12=angles['h12'], qf12=angles['qf2'], hf2=angles['hf2'], 
                                    qin2=angles['qin2'], hin2=angles['hin2'], 
                                    m1=angles['m1'], m2=angles['m2'], m3=angles['m3'])
    # Create a figure with 4 subplots (2 rows, 3 columns) with larger dimensions
    if len(normalized_data.keys()) % 2 == 0:
        fig, axes = plt.subplots(int(len(normalized_data.keys())/2), 2, figsize=(28, 20))
        axes = axes.ravel()  
        multi=True
    else:
        fig, axes = plt.subplots(int(len(normalized_data.keys())), 1, figsize=(28, 20))

    # Iterate over each basis in the recorded data via key "H" etc
    for i, basis in enumerate(normalized_data.keys()):
        targetProb = cml.UnitaryToProb(searchMatrix, measurement_basis, measurement_basis[basis])    
        labels = list(measurement_basis.keys())
        measured_values = [normalized_data[basis][k][0] for k in labels]
        err = [normalized_data[basis][k][1] for k in labels]
        theoretical_values = [targetProb[k] for k in labels]
        x = np.arange(len(normalized_data[basis].keys()))  

        if multi==True:
            ax = axes[i]
        else:
            ax = axes

        bar_width = 0.35  
        
        # ax.bar(x, measured_values, width=bar_width, color='gold', label='Measured')
        bars = ax.bar(x, measured_values, width=bar_width, color='gold', label='Measured')
        for j, bar in enumerate(bars):
            height = bar.get_height()
            raw_val, raw_err = data[basis][labels[j]]  # unpack the tuple
            count = float(raw_val * 1000)      # mV
            count_err = float(raw_err * 1000)  # mV

            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + 0.05,
                f"{count:.2f} ± {count_err:.2f} mV",
                ha="center",
                va="bottom",
                fontsize=15
            )
       
        ax.bar(x, theoretical_values, width=bar_width, color='none', edgecolor='black', linestyle=':', linewidth=2, label='Theoretical')
       
        ax.set_title(f'|{basis}⟩ Input', fontsize = 30)
        ax.errorbar(labels, measured_values, yerr=err, fmt='s', color='k')
        ax.set_xlabel('State', fontsize=30)
        ax.set_ylabel('Probability', fontsize=30)
        ax.set_ylim(0, 1)
        ax.set_xticks(x + bar_width / 2)
        ax.set_xticklabels(labels, fontsize=30)
        ax.tick_params(axis='y')
        ax.legend(fontsize=20)

        fit += np.linalg.norm(np.array(measured_values) - np.array(theoretical_values))
    title = graph_title + f" | Fit: {fit:.2f}"
    # plt.suptitle(title, fontweight='bold', fontsize=28)
    plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05, wspace=0.25, hspace=0.3)

    if plot_type is not None:      
        directory_name = datetime.datetime.now().strftime(f"Figures/Figures_%Y-%m-%d/{plot_type}_Figures_%Y-%m-%d/%Y-%m-%d__%H-%M")
    else: directory_name = datetime.datetime.now().strftime("Figures/Figures_%Y-%m-%d/%Y-%m-%d__%H-%M")

    if note is not None:
        directory_name = f'{note}_{directory_name}'

    if save_plot==True:
        try:
            savePlot(fig, graph_title='', filepath=directory_name)
        except Exception as e:
            print(f"Error saving plot: {e} \n\n Trying again...")
            try:
                savePlot(fig, graph_title=graph_title, filepath=directory_name)
            except Exception as e:
                print(f"Failed saving plot: {e}")
        print(f"Plot saved to directory: {directory_name}")

    if save_data == True:
        try:
            saveData(graph_title='', data=data, normalised_data=normalized_data, angles=angles, filepath=directory_name, plot_type=plot_type)
        except Exception as e:
            print(f"Error saving data: {e} \n\n Trying again...")  
            try:
                saveData(graph_title=graph_title, data=data, normalised_data=normalized_data, angles=angles, filepath=directory_name, plot_type=plot_type)
            except Exception as e:
                print(f"Failed saving data: {e}")
    print(f"Data saved to directory: {directory_name}")
    
    if show_plot ==True:
        plt.show()
   
    print(f"Measured value solution fit: {fit}")

def plot_single(data, graph_title, angles,  save_plot=True, save_data=True, show_plot=True):

    input = data.keys()
    measurement_basis = basis_vectors
    # normalized_data = cml.normalise_full_tomo_data(data)
    searchMatrix = cml.getUnitary(q1=angles['q1'], h1=angles['h1'], q12=angles['q12'], 
                                    h12=angles['h12'], qf12=angles['qf2'], hf2=angles['hf2'], 
                                    qin2=angles['qin2'], hin2=angles['hin2'], 
                                    m1=angles['m1'], m2=angles['m2'], m3=angles['m3'])
    
    # normalized_data = cml.normalise_measurements(data)
    normalized_data = cml.normalise_full_tomo_data(data)
    fit = 0
    fig, ax = plt.subplots(figsize=(14, 8))

    targetProb = cml.UnitaryToProb(searchMatrix, measurement_basis, measurement_basis[input])
    labels = list(measurement_basis.keys())
    measured_values = [normalized_data[k][0] for k in labels]
    err = [normalized_data[k][1] for k in labels]
    theoretical_values = [targetProb[k] for k in labels]
    x = np.arange(len(labels))  

    bar_width = 0.35  
    ax.bar(x, measured_values, width=bar_width, color='gold', label='Measured')
    ax.bar(x, theoretical_values, width=bar_width, color='none', edgecolor='black', linestyle=':', linewidth=3, label='Theoretical')
    ax.errorbar(x, measured_values, yerr=err, fmt='s', color='k')
    ax.set_xlabel('State', fontsize=20)
    ax.set_ylabel('Probability', fontsize=20)
    ax.set_xticks(x, labels, fontsize=15)
    ax.set_ylim(0, 1)
    ax.tick_params(axis='y')
    ax.legend(fontsize=15)
    fit += np.linalg.norm(np.array(measured_values) - np.array(theoretical_values))
    plt.title(f"{graph_title} | Input: |{input}⟩ | Fit: {fit:.2f}", fontweight='bold', fontsize=25)
    fig.tight_layout()

    directory_name = datetime.datetime.now().strftime("Figures/Figures_%Y-%m-%d/%Y-%m-%d__%H-%M")
    if save_plot==True:
        savePlot(fig, graph_title=graph_title, filepath=directory_name)
    if save_data == True:
        saveData(graph_title=graph_title, data=data, normalised_data=normalized_data, angles=angles, filepath=directory_name)
    if show_plot ==True:
        plt.show()

    plt.show()

def plot_mirror(normalized_data, categories):
    # Create a figure with 3 subplots for each set of measurements (M1, M2, M3)
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))  # 1 row, 3 columns
    axes = axes.ravel()

    # Iterate over normalized data sets (M1, M2, M3) and plot the respective normalized values
    for i, (key, measurements) in enumerate(normalized_data.items()):
        normalized_values = [measurements[cat] for cat in categories]
        axes[i].bar(np.arange(len(categories)), normalized_values, color='gold', label=key)
        axes[i].set_ylim(0, 1)
        axes[i].set_title(f'{key} Normalized Measurements')
        axes[i].set_xlabel('State')
        axes[i].set_ylabel('Normalized Power')
        axes[i].set_xticks(np.arange(len(categories)))
        axes[i].set_xticklabels(categories)
        axes[i].legend()

    plt.tight_layout()
    plt.show()

