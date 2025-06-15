import { UseFormRegister, FieldErrors } from 'react-hook-form';
import { EyeIcon, KeyIcon, PlayIcon, Cog6ToothIcon, TrashIcon } from '@heroicons/react/24/outline';
import { LoadingSpinner } from './LoadingSpinner';
import { cn } from '@/lib/utils';

interface FormData {
  videoId: string;
  maxResults: number;
  dryRun: boolean;
}

interface SpamDetectionFormProps {
  register: UseFormRegister<FormData>;
  errors: FieldErrors<FormData>;
  isLoading: boolean;
  showAdvanced: boolean;
  onAdvancedToggle: () => void;
  onSubmit: (e?: React.BaseSyntheticEvent) => Promise<void>;
  extractVideoId: (url: string) => string;
  handleVideoUrlChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  isDryRun: boolean;
}

export function SpamDetectionForm({
  register,
  errors,
  isLoading,
  showAdvanced,
  onAdvancedToggle,
  onSubmit,
  extractVideoId,
  handleVideoUrlChange,
  isDryRun
}: SpamDetectionFormProps) {
  return (
    <form onSubmit={onSubmit} className="space-y-6">
      {/* Video URL/ID Section */}
      <div>
        <label htmlFor="videoId" className="block text-sm font-medium text-gray-700 mb-2">
          <PlayIcon className="h-4 w-4 inline mr-1" />
          YouTube Video URL or ID
        </label>
        <input
          {...register('videoId')}
          type="text"
          id="videoId"
          className={cn(
            'input w-full',
            errors.videoId && 'border-red-300 focus:border-red-500 focus:ring-red-500'
          )}
          placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ or dQw4w9WgXcQ"
          onChange={handleVideoUrlChange}
        />
        {errors.videoId && (
          <p className="mt-1 text-sm text-red-600">{errors.videoId.message}</p>
        )}
      </div>

      {/* Advanced Options */}
      <div>
        <button
          type="button"
          onClick={onAdvancedToggle}
          className="flex items-center text-sm text-primary-600 hover:text-primary-700 font-medium"
        >
          <Cog6ToothIcon className="h-4 w-4 mr-1" />
          Advanced Options
          <svg
            className={cn(
              'ml-1 h-4 w-4 transform transition-transform',
              showAdvanced ? 'rotate-180' : ''
            )}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {showAdvanced && (
          <div className="mt-4 space-y-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <label htmlFor="maxResults" className="block text-sm font-medium text-gray-700 mb-2">
                Max Comments to Process
              </label>
              <input
                {...register('maxResults', { valueAsNumber: true })}
                type="number"
                id="maxResults"
                min="1"
                max="200"
                className="input w-full"
                placeholder="50"
              />
              <p className="mt-1 text-xs text-gray-500">
                Maximum number of comments to analyze (1-200)
              </p>
            </div>

            <div className="flex items-center">
              <input
                {...register('dryRun')}
                type="checkbox"
                id="dryRun"
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="dryRun" className="ml-2 block text-sm text-gray-700">
                <EyeIcon className="h-4 w-4 inline mr-1" />
                Dry Run (Preview only - don't delete comments)
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Production Warning */}
      {!isDryRun && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start">
            <svg className="h-5 w-5 text-yellow-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">Production Mode Warning</h3>
              <p className="mt-1 text-sm text-yellow-700">
                You are running in production mode. Detected spam comments will be permanently deleted from YouTube.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className={cn(
          'btn btn-primary w-full flex items-center justify-center',
          isLoading && 'opacity-50 cursor-not-allowed'
        )}
      >
        {isLoading ? (
          <>
            <LoadingSpinner size="sm" className="mr-2" />
            {isDryRun ? 'Analyzing Comments...' : 'Processing & Deleting Spam...'}
          </>
        ) : (
          <>
            {isDryRun ? (
              <>
                <EyeIcon className="h-4 w-4 mr-2" />
                Analyze Comments (Preview)
              </>
            ) : (
              <>
                <TrashIcon className="h-4 w-4 mr-2" />
                Delete Spam Comments
              </>
            )}
          </>
        )}
      </button>
    </form>
  );
}