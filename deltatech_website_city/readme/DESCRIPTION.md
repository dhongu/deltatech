# Website City Selection

This module enhances the website checkout process by providing a dynamic city selection feature based on the selected state/region.

## Features

- **Dynamic City Selection**: Users can select their city from a predefined list that automatically updates based on the selected state
- **Smart Field Display**: Automatically toggles between city dropdown and text input based on data availability
- **Improved Address Layout**: Reorders address fields in a logical sequence (Country → State → City → Street)
- **Enhanced User Experience**: Reduces typing errors and ensures consistent address data entry
- **AJAX Integration**: Real-time loading of cities without page refresh when state selection changes

## Technical Details

- Extends the website sale checkout functionality
- Uses RPC calls to dynamically load city data based on state selection
- Automatically hides/shows city fields based on available options
- Maintains compatibility with existing address validation workflows

## Use Cases

- E-commerce websites requiring accurate delivery addresses
- Regional businesses with state/city-specific services
- Websites needing structured location data for logistics optimization
