# Research Brief Generator - Frontend

A modern, professional Next.js frontend for the Context-Aware Research Brief Generator. Built with TypeScript, Tailwind CSS, and Heroicons for a beautiful and responsive user interface.

## Features

- **Dashboard**: Overview with metrics, system status, and quick actions
- **Chat Interface**: Interactive research assistant with real-time messaging
- **Brief Generator**: Form-based research brief generation with depth options
- **History**: View and download past research briefs
- **Settings**: System information and configuration management
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Heroicons
- **Charts**: Recharts (for future analytics)
- **State Management**: React hooks and localStorage

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running (see backend README)

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
# Copy the example environment file
cp .env.local.example .env.local

# Edit .env.local and set your backend URL
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router pages
│   │   ├── page.tsx        # Dashboard
│   │   ├── chat/           # Chat interface
│   │   ├── brief/          # Brief generator
│   │   ├── history/        # History view
│   │   └── settings/       # Settings page
│   ├── components/         # Reusable components
│   │   └── Layout.tsx     # Main layout with navigation
│   ├── lib/               # Utility libraries
│   │   └── api.ts         # API client
│   └── types/             # TypeScript type definitions
│       └── index.ts       # Application types
├── public/                # Static assets
├── .env.local            # Environment variables
└── package.json          # Dependencies and scripts
```

## Environment Variables

Create a `.env.local` file in the frontend directory:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Features Overview

### Dashboard
- System health monitoring
- User statistics and metrics
- Quick action buttons
- Backend connection status

### Chat Interface
- Real-time messaging with the research assistant
- Message history with timestamps
- Loading states and error handling
- Responsive chat bubbles

### Brief Generator
- Topic input with validation
- Research depth selection (shallow, moderate, deep)
- Follow-up query option
- Additional context field
- Real-time generation with progress indicators
- Download generated briefs as JSON

### History
- View all past research briefs
- Brief summaries and key insights
- Download individual briefs
- Date and source information

### Settings
- System information display
- Model configuration details
- Backend URL configuration
- Local data management
- About section with version info

## API Integration

The frontend communicates with the backend through a RESTful API:

- **Health Check**: `/health`
- **Generate Brief**: `POST /brief`
- **Chat Response**: `POST /chat`
- **User History**: `GET /user/{user_id}/history`
- **User Stats**: `GET /user/{user_id}/stats`
- **Available Models**: `GET /models`

## User Experience

- **Professional Design**: Clean, modern interface with consistent styling
- **Responsive Layout**: Works on all screen sizes
- **Loading States**: Smooth loading indicators for better UX
- **Error Handling**: Graceful error messages and fallbacks
- **Accessibility**: Proper ARIA labels and keyboard navigation
- **Mobile-First**: Optimized for mobile devices

## Development

### Adding New Pages

1. Create a new directory in `src/app/`
2. Add a `page.tsx` file
3. Import and use the `Layout` component
4. Add navigation item in `src/components/Layout.tsx`

### Styling

The project uses Tailwind CSS for styling. Key design tokens:

- **Primary Color**: Indigo (`indigo-600`)
- **Background**: Gray (`gray-50`, `gray-100`)
- **Text**: Gray scale (`gray-900`, `gray-700`, `gray-500`)
- **Borders**: Gray (`gray-200`, `gray-300`)

### State Management

- **Local State**: React hooks (`useState`, `useEffect`)
- **Persistence**: localStorage for user ID and preferences
- **API State**: Custom hooks for data fetching

## Deployment

### Vercel (Recommended)

1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

### Other Platforms

1. Build the project: `npm run build`
2. Start the production server: `npm run start`
3. Set environment variables for your platform

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
