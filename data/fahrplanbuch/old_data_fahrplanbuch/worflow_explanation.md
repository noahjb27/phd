current situation (12.12.24):
I am modelling snapshots of the networks in different years. The data for these are in modeling/1_data_fahrplanbuch and then in seperate snaptshot folders with pattern YEAR-network. 
In YEAR-network folders I have the following files:
- line_data_year.csv which has the transcription of the data for the snapshot.

Line description,1946,Stops,Frequency,Length (time)
1_bus_both/unkown,1946,"Flughafen - Alt-Friedrichsfelde (Rosenfelder Strasse) (69)",25,

I then use the jupyter notebook retrieve-table-to-df.ipynb in the folder to convert the csv file into a dataframe and save it to stops_df_year-initial.csv
,stop_name,line_count,type,in_lines
0,Flughafen,1,bus,['1']
- I could do datatype checks on this file?

I use modeling\1_data_fahrplanbuch\1946-network\combine_stops_df.ipynb to combine the stops_df_year-initial.csv with the  
../final-tables/stops_table.csv which has the values for all snapshots combined so far. I make some checks between the two files and if there are matches I copy the geolocation from stop_table.csv to the initial dataframe and save it to 1946-stops-combined.csv

,stop_name,type,in_lines,location,identifier,previous_in_lines,stop_description
0,Adlershof,s-bahn,"['KBS 100a', 'KBS 100c']","52.434722222222,13.541388888889",Q323551,"['KBS 100a', 'KBS 103']+ ['KBS 100a', 'KBS 103']+ KBS 103,KBS 100a+ KBS 103,KBS 100a,KBS 106+ KBS 106a,KBS 103,KBS 103a",nan+ nan+ Berlin-Adlershof station+ Berlin-Adlershof station+ Berlin-Adlershof station
1,Akazienallee,bus,['D'],,,,
2,Alexanderplatz,bus,"['1', '9']",,,,
3,Alexanderplatz,s-bahn,"['KBS 101', 'KBS 100c']","52.521388888889,13.411944444444",Q111324700,"['KBS 101', 'KBS 103', 'KBS 102']+ ['KBS 102', 'KBS 101', 'KBS 103']+ KBS 102,KBS 103,KBS 101+ KBS 101,KBS 103,KBS 102+ KBS 101,KBS 102,KBS 103,KBS 103a,KBS 104",nan+ nan+ S-Bahnhof Berlin Alexanderplatz+ S-Bahnhof Berlin Alexanderplatz+ S-Bahnhof Berlin Alexanderplatz
4

I then do some manual geolocalisation of the stops with no localisation (because they did not match with the overall stops_table.csv). I save this file as stops_df_year-final.csv - This is an important file because all stations have not been localised. In table-creation-year.ipynb I use stops_df_year-final.csv to create three seperate files that are referencing each other using the ids: line_stops_df.to_csv("line_stops_1946-final.csv")
line_df.to_csv("line_df_1946-final.csv")
df_stops.to_csv("stops_df_1946-final.csv")

Above the snapshot directory I have a final-tables directory where I have combine-tables.ipynb where the snapshot files are concatenated. 

Then in a sister folder I have 2_enriched_data where data-enrichment.ipynb adds some external data to enriched-data/lines_enriched.csv and enriched-data/stations_enriched.csv

This workflow is very fragile and if I rerun code I might lose data. It is also really messy with a lot of files being generated. Ideally I clean this all up. Some of the snapshots are also a bit different particularly the ones for 1960, 1961 and 1964 because these were the first ones and I did not use the combinining stops localisation method yet since I did not have enough data to cross reference. I think the key files are the line_data_year.csv files sinces this is where the transcription is of all the base data. and then also the stops_df_year-final.csv since this is where all the data is on the first round of geolocalisation of stations.

How can make my files cleaner and how can I improve the flow of this do you have any thoughts?