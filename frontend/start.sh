#!/bin/bash
npm run build
npx serve -s build -l ${PORT:-3000}