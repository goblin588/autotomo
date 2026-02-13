import Libraries.DataProcessingLib as dpl
import Libraries.CharPlotLib as cpl
import Libraries.AngMenu as am



if __name__ == "__main__":
    angles = am.angle_menu()
    filepath = input("Enter filepath to characterisation data: ")
    try:
        data = dpl.load_csv_data(filepath)
        avg_data = dpl.average_measurements(data['raw_data']) 
        cpl.plot_characterisation(avg_data, f'Avg\'d {angles['title']}', angles=angles )
    except Exception as e:
        print(f'Error occured: {e}')
