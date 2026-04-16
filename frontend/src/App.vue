<template>
  <div class="min-h-screen bg-gray-950">
    <!-- Navigation -->
    <nav class="bg-gray-900 border-b border-gray-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center">
            <router-link to="/" class="text-xl font-bold text-white">
              10<span class="text-green-400">Predict</span>
            </router-link>
            <div class="ml-10 flex items-baseline space-x-4">
              <router-link
                to="/"
                class="px-3 py-2 rounded-md text-sm font-medium"
                :class="$route.name === 'dashboard' ? 'bg-gray-800 text-white' : 'text-gray-300 hover:text-white'"
              >
                Dashboard
              </router-link>
              <router-link
                to="/predictions"
                class="px-3 py-2 rounded-md text-sm font-medium"
                :class="$route.name === 'predictions' ? 'bg-gray-800 text-white' : 'text-gray-300 hover:text-white'"
              >
                Predictions
              </router-link>
              <router-link
                to="/research"
                class="px-3 py-2 rounded-md text-sm font-medium"
                :class="$route.name === 'research' ? 'bg-gray-800 text-white' : 'text-gray-300 hover:text-white'"
              >
                Research
              </router-link>
            </div>
          </div>
          <div class="text-sm text-gray-400">
            Chain-of-Effects Penny Stock Intelligence
          </div>
        </div>
      </div>
    </nav>

    <!-- Main content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <router-view />
    </main>
  </div>
</template>
