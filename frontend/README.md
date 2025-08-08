# Job Matcher Frontend

A modern React application for uploading resumes and finding job matches. Built with TypeScript, Material-UI, and Firebase Authentication.

## Features

- 🔐 **Firebase Authentication** - Secure login and signup
- 📄 **Resume Upload** - Support for PDF, TXT, and DOCX files
- 🔍 **Resume Parsing** - AI-powered resume analysis
- 💼 **Job Matching** - Find relevant job opportunities
- 📊 **Dashboard** - Overview of resumes and statistics
- 🎨 **Modern UI** - Beautiful Material-UI design
- 📱 **Responsive** - Works on desktop and mobile

## Tech Stack

- **React 18** with TypeScript
- **Material-UI v5** for components and theming
- **TanStack Query v4** for data fetching
- **React Router v6** for navigation
- **Firebase v10** for authentication
- **React Dropzone** for file uploads
- **Notistack** for notifications

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Environment Variables:**
   Create a `.env` file in the frontend directory with:
   ```
   # Firebase Configuration
   REACT_APP_FIREBASE_API_KEY=your_firebase_api_key
   REACT_APP_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
   REACT_APP_FIREBASE_PROJECT_ID=your_project_id
   REACT_APP_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
   REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_messaging_sender_id
   REACT_APP_FIREBASE_APP_ID=your_app_id

   # API Configuration
   REACT_APP_API_BASE_URL=http://localhost:8000
   ```

3. **Start development server:**
   ```bash
   npm start
   ```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Navbar.tsx     # Navigation bar
│   └── ProtectedRoute.tsx # Route protection
├── contexts/           # React contexts
│   └── AuthContext.tsx # Firebase authentication
├── firebase/           # Firebase configuration
│   └── config.ts
├── pages/              # Page components
│   ├── Dashboard.tsx   # Main dashboard
│   ├── JobMatches.tsx  # Job matching results
│   ├── Login.tsx       # Authentication
│   └── ResumeUpload.tsx # File upload
├── services/           # API services
│   └── api.ts         # API client and types
└── App.tsx            # Main app component
```

## Key Improvements

### UI/UX Enhancements
- **Modern Design**: Clean, professional Material-UI theme
- **Loading States**: Skeleton loaders and progress indicators
- **Error Handling**: Comprehensive error messages and notifications
- **Responsive Layout**: Mobile-friendly design
- **Visual Feedback**: Icons, colors, and animations

### Technical Improvements
- **TanStack Query v4**: Modern data fetching with caching
- **Type Safety**: Full TypeScript implementation
- **Error Boundaries**: Graceful error handling
- **Performance**: Optimized re-renders and queries
- **Accessibility**: ARIA labels and keyboard navigation

### Features
- **File Upload**: Drag-and-drop resume upload
- **Resume Management**: View, parse, and delete resumes
- **Job Matching**: AI-powered job recommendations
- **User Authentication**: Secure Firebase auth
- **Real-time Updates**: Live data synchronization

## Development

### Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App

### Code Quality

The project uses:
- **TypeScript** for type safety
- **ESLint** for code linting
- **Prettier** for code formatting
- **Material-UI** for consistent design

## Deployment

The frontend is containerized and can be deployed to:
- **Docker**: Use the provided Dockerfile
- **GKE**: Kubernetes deployment included
- **Cloud Run**: Serverless deployment option

## Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Include error handling and loading states
4. Test on mobile devices
5. Update documentation as needed
