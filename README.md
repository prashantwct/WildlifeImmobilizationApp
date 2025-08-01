# Wildlife Immobilization App

A Progressive Web App (PWA) designed for wildlife immobilization case management and monitoring. The app helps track drug administration, vital signs, and events during wildlife immobilization procedures.

## Features

- **Case Management**: Create and manage wildlife immobilization cases
- **Drug Repository**: Pre-populated with common wildlife drugs and dosages
- **Species Database**: Built-in database of common wildlife species
- **Event Monitoring**: Track key events during immobilization (drug administration, induction, revival, etc.)
- **Offline Support**: Works without internet connection (PWA)
- **Export Functionality**: Export case data as PDF

## Pre-populated Data

### Drugs
- Ketamin (100 mg/ml)
- Meditomedine (20 mg/ml)
- Atipomezol (5 mg/ml)

### Species
- Tiger
- Leopard
- Sloth Bear

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/prashantwct/WildlifeImmobilizationApp.git
   cd WildlifeImmobilizationApp
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

1. **Case Management**: Create new cases or view existing ones
2. **Drug Calculator**: Calculate drug dosages based on animal weight
3. **Monitoring**: Record events and vital signs during procedures
4. **Case History**: View and export previous cases

## Technologies Used

- React
- PWA (Progressive Web App)
- Local Storage
- jsPDF (for PDF exports)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
