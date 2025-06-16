'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import { 
  PlayIcon, 
  ShieldCheckIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  EyeIcon,
  TrashIcon,
  ClockIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

import { VideoInfo } from '@/components/VideoInfo';
import { ResultsDisplay } from '@/components/ResultsDisplay';
import { StatsCard } from '@/components/StatsCard';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { AuthStatus } from '@/components/AuthStatus';
import { useSpamDetection } from '@/hooks/useSpamDetection';
import { useVideoInfo } from '@/hooks/useVideoInfo';
import { extractVideoIdFromUrl } from '@/lib/api';

const formSchema = z.object({
  videoId: z.string().min(11, 'Valid YouTube video ID is required').max(11, 'Invalid video ID length'),
  maxResults: z.number().min(1).max(200).default(50),
  dryRun: z.boolean().default(true),
});

type FormData = z.infer<typeof formSchema>;

export default function HomePage() {
  const [results, setResults] = useState<any>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
    setValue,
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      maxResults: 50,
      dryRun: true,
    },
  });

  const watchedVideoId = watch('videoId');
  const watchedDryRun = watch('dryRun');

  const spamDetectionMutation = useSpamDetection();
  const { data: videoInfo, isLoading: videoInfoLoading } = useVideoInfo(
    watchedVideoId
  );

  const onSubmit = async (data: FormData) => {
    try {
      const result = await spamDetectionMutation.mutateAsync({
        video_id: data.videoId,
        max_results: data.maxResults,
        dry_run: data.dryRun,
      });
      
      setResults(result);
      
      if (result.success) {
        const spam_detected = result.summary?.spam_detected || 0;
        const comments_deleted = result.processing_stats?.deleted_count || 0;
        if (data.dryRun) {
          toast.success(`Analysis complete! Found ${spam_detected} spam comments`);
        } else {
          // toast.success(`Deleted ${comments_deleted} spam comments successfully!`);
          toast.success(`Deleted all spam comments successfully!`);
        }
      } else {
        toast.error(result.errors?.[0] || 'Processing failed');
      }
    } catch (error: any) {
      toast.error(error.message || 'An error occurred');
    }
  };

  const handleVideoUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const videoId = extractVideoIdFromUrl(value);
    setValue('videoId', videoId);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <div className="flex justify-center mb-6">
          <div className="p-4 bg-primary-100 rounded-full">
            <ShieldCheckIcon className="h-12 w-12 text-primary-600" />
          </div>
        </div>
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          AI-Powered YouTube Spam Detector
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
          Automatically detect and remove online gambling spam comments from your YouTube videos 
          using advanced AI technology powered by Google Gemini.
        </p>
        
        {/* Feature highlights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          <div className="flex items-center justify-center space-x-3 p-4 bg-white rounded-lg shadow-sm border">
            <EyeIcon className="h-6 w-6 text-primary-600" />
            <span className="text-sm font-medium text-gray-700">Smart Detection</span>
          </div>
          <div className="flex items-center justify-center space-x-3 p-4 bg-white rounded-lg shadow-sm border">
            <TrashIcon className="h-6 w-6 text-danger-600" />
            <span className="text-sm font-medium text-gray-700">Auto Removal</span>
          </div>
          <div className="flex items-center justify-center space-x-3 p-4 bg-white rounded-lg shadow-sm border">
            <ChartBarIcon className="h-6 w-6 text-success-600" />
            <span className="text-sm font-medium text-gray-700">Detailed Analytics</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Form */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="card-header">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                <PlayIcon className="h-5 w-5 mr-2 text-primary-600" />
                Spam Detection Configuration
              </h2>
            </div>
            <div className="card-body">
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                {/* Video URL/ID */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    YouTube Video URL or ID
                  </label>
                  <input
                    type="text"
                    onChange={handleVideoUrlChange}
                    className={`input ${errors.videoId ? 'input-error' : ''}`}
                    placeholder="https://youtu.be/dQw4w9WgXcQ or dQw4w9WgXcQ"
                  />
                  <input type="hidden" {...register('videoId')} />
                  {errors.videoId && (
                    <p className="mt-1 text-sm text-danger-600">{errors.videoId.message}</p>
                  )}
                </div>

                {/* Advanced Options */}
                <div>
                  <button
                    type="button"
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    className="flex items-center text-sm text-primary-600 hover:text-primary-700"
                  >
                    <InformationCircleIcon className="h-4 w-4 mr-1" />
                    {showAdvanced ? 'Hide' : 'Show'} Advanced Options
                  </button>
                  
                  {showAdvanced && (
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Max Comments to Process
                        </label>
                        <input
                          type="number"
                          {...register('maxResults', { valueAsNumber: true })}
                          min="1"
                          max="200"
                          className="input"
                        />
                        <p className="mt-1 text-xs text-gray-500">
                          Maximum number of comments to analyze (1-200)
                        </p>
                      </div>
                      
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          {...register('dryRun')}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                        <label className="ml-2 block text-sm text-gray-700">
                          Dry Run (Preview only - don't delete comments)
                        </label>
                      </div>
                      
                      {/* Authentication Status */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Authentication Status
                        </label>
                        <AuthStatus onAuthChange={setIsAuthenticated} />
                      </div>
                    </div>
                  )}
                </div>

                {/* Mode Warning */}
                {!watchedDryRun && (
                  <div className="flex items-start space-x-3 p-4 bg-warning-50 border border-warning-200 rounded-lg">
                    <ExclamationTriangleIcon className="h-5 w-5 text-warning-600 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-medium text-warning-800">Production Mode Active</h4>
                      <p className="text-sm text-warning-700 mt-1">
                        Comments will be permanently deleted. {!isAuthenticated && 'Authentication required.'}
                      </p>
                    </div>
                  </div>
                )}
                
                {/* Authentication Required Warning */}
                {!watchedDryRun && !isAuthenticated && (
                  <div className="flex items-start space-x-3 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <ExclamationTriangleIcon className="h-5 w-5 text-red-600 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-medium text-red-800">Authentication Required</h4>
                      <p className="text-sm text-red-700 mt-1">
                        You must authenticate with your YouTube account to delete comments. Please login above.
                      </p>
                    </div>
                  </div>
                )}

                {/* Submit Button */}
                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={spamDetectionMutation.isPending || (!watchedDryRun && !isAuthenticated)}
                    className="btn-primary btn-lg flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {spamDetectionMutation.isPending ? (
                      <>
                        <LoadingSpinner size="sm" />
                        <span>Processing...</span>
                      </>
                    ) : (
                      <>
                        <ShieldCheckIcon className="h-5 w-5" />
                        <span>{watchedDryRun ? 'Analyze Comments' : 'Remove Spam'}</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Video Info */}
          {watchedVideoId && watchedVideoId.length === 11 && (
            <VideoInfo 
              videoId={watchedVideoId} 
              isLoading={videoInfoLoading}
              data={videoInfo}
            />
          )}

          {/* Quick Stats */}
          {results && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Quick Stats</h3>
              <div className="grid grid-cols-1 gap-4">
                <StatsCard
                  title="Comments Processed"
                  value={results.summary?.total_comments || 0}
                  icon={<ChartBarIcon className="h-5 w-5 text-primary-600" />}
                />
                <StatsCard
                  title="Spam Detected"
                  value={results.summary?.spam_detected || 0}
                  icon={<ExclamationTriangleIcon className="h-5 w-5 text-red-600" />}
                />
                {/* <StatsCard
                  title="Comments Deleted"
                  value={results.processing_stats?.deleted_count || 0}
                  icon={<TrashIcon className="h-5 w-5 text-green-600" />}
                /> */}
              </div>
            </div>
          )}

          {/* Help Section */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900">Need Help?</h3>
            </div>
            <div className="card-body space-y-3">
              <div className="text-sm text-gray-600">
                <h4 className="font-medium text-gray-900 mb-2">Getting API Keys:</h4>
                <ul className="space-y-1 list-disc list-inside">
                  <li>
                    <a 
                      href="https://console.developers.google.com/" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-primary-600 hover:text-primary-700"
                    >
                      YouTube Data API v3
                    </a>
                  </li>
                  <li>
                    <a 
                      href="https://makersuite.google.com/app/apikey" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-primary-600 hover:text-primary-700"
                    >
                      Google Gemini API
                    </a>
                  </li>
                </ul>
              </div>
              
              <div className="text-sm text-gray-600">
                <h4 className="font-medium text-gray-900 mb-2">Tips:</h4>
                <ul className="space-y-1 list-disc list-inside">
                  <li>Always test with dry run first</li>
                  <li>Start with smaller comment batches</li>
                  <li>Monitor the results carefully</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Results Section */}
      {results && (
        <div className="mt-12">
          <ResultsDisplay data={results} isDryRun={watch('dryRun')} />
        </div>
      )}
    </div>
  );
}