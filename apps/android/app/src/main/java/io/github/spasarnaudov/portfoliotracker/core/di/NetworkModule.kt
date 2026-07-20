package io.github.spasarnaudov.portfoliotracker.core.di

import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import io.github.spasarnaudov.portfoliotracker.core.network.ApiService
import io.github.spasarnaudov.portfoliotracker.core.network.DynamicApiServiceHolder

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    /**
     * Intentionally unscoped: every injection site should ask for `Provider<ApiService>`
     * and call `.get()` per request, so a base-URL change (which rebuilds the client
     * inside [DynamicApiServiceHolder]) is picked up immediately instead of being
     * frozen at the first injection.
     */
    @Provides
    fun provideApiService(holder: DynamicApiServiceHolder): ApiService = holder.current
}
