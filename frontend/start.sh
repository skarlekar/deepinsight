#!/bin/bash
echo "Starting DeepInsight Frontend build process..."
npm run build
echo "Build complete, starting serve..."
npx serve -s build -l ${PORT:-3000}