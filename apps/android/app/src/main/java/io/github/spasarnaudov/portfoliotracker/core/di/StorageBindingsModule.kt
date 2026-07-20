package io.github.spasarnaudov.portfoliotracker.core.di

import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import io.github.spasarnaudov.portfoliotracker.core.auth.KeystoreTokenStorage
import io.github.spasarnaudov.portfoliotracker.core.auth.TokenStorage
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class StorageBindingsModule {
    @Binds
    @Singleton
    abstract fun bindTokenStorage(impl: KeystoreTokenStorage): TokenStorage
}
