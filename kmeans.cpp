#include <bits/stdc++.h>
#include <vector>
#include <cmath>
#include <stdlib.h>
#include <iostream>
#include <time.h>
#include <algorithm>
using namespace std;

#define CONV 0.1;

template <typename T>
void printMatrix(vector<vector<T>> &m){
  for (int i = 0; i < m.size(); i++){
    for (int j = 0; j < m.at(i).size(); j++){
      cout << m[i][j]<<"\t ";
    }
    cout<<endl;
  }
}

vector<vector<double>> parseCSV(){
    ifstream  data("Iris.csv");
    string line;
    vector<vector<double> > parsedCsv;
    while(getline(data,line))
    {
        stringstream lineStream(line);
        string cell;
        vector<double> parsedRow;
        while(getline(lineStream,cell,','))
        {
            double value = stod(cell);
            parsedRow.push_back(value);
        }

        parsedCsv.push_back(parsedRow);
    }
    cout << parsedCsv.size() << endl;
    //cout << parsedCsv[0][0]<<"\t ";
    //printMatrix(parsedCsv);
    return parsedCsv;
}



template <typename T>
void fillVector(vector<vector<T>> &m, int row, int col){
  for (int i = 0; i < row; i++){
    vector<T> v;
    m.push_back(v);
    for (int j = 0; j < col; j++){
      int n = rand()%11;
      T n_t = (T)(rand() % 100)/100;
      n_t += n;
      m.at(i).push_back(n_t);
    }
  }
  printMatrix(m);
}

template <typename T>
void print(vector<T> const &input)
{
    for (int i = 0; i < input.size(); i++) {
        std::cout << input.at(i) << ' ';
    }
}

template <typename T>
T distance(vector<T> &vector1, vector<T> &vector2) {

  //static_assert(vector1.size() == vector2.size());

  T count = 0;
  for (int i = 0; i < vector1.size(); i++) {
      T d = vector1.at(i) - vector2.at(i);
      d = pow(d, 2);
      count += d;
  }

  count = sqrt(count);

  return count;
}

template <typename T>
vector<T> matDistance(vector<vector<T>> &matrix, vector<T> &v) {

  vector<T> re;
  for (int i = 0; i < matrix.size(); i++) {
    T dis = distance(v, matrix.at(i));
    re.push_back(dis);
  }

  return re;
}



template <typename T>
T vector_magnitude(vector<T> &v) {
  T magnitude_v;
  for(int i=0; i<v.size(); i++) {
    magnitude_v += pow(v.at(i), 2);
  }

  magnitude_v = sqrt(magnitude_v);
  return magnitude_v;
}

template <typename T>
bool check_convergence(vector<T> &a, vector<T> &b) {
  // Will be used the formula to find the magnitude of a vector
  T magnitude_a = vector_magnitude(a);
  T magnitude_b = vector_magnitude(b);
  cout << "M-a: " << magnitude_a << "M-b: " << magnitude_b << '\n';
  if (abs(magnitude_a - magnitude_b) <= 0.5) {return true;}
  else {return false;}
}

struct compare
{
    int key;
    compare(int const &i): key(i) {}

    bool operator()(int const &i) {
        return (i == key);
    }
};

template <typename T>
vector<vector<int>> kmeans(vector<vector<T>> &matrix) {
  int n_clusters = matrix.size() * 0.2;
  cout << "Number of clusters: " << n_clusters << endl;

  vector<int> centroid_indices;

  int n_centroids = 0;
  while (n_centroids < n_clusters) {
    int new_index = rand() %(matrix.size());

    // Condición para que no se repita un mismo centroide
    if (!(find_if(centroid_indices.begin(), centroid_indices.end(), compare(new_index)) != centroid_indices.end())) {
      centroid_indices.push_back(new_index);
      n_centroids++;
    }

  }

  cout << "Indices de clusters" << endl;
  for(int i =0; i < centroid_indices.size(); i++) {
    cout << centroid_indices[i] << " ";
  }
  cout << endl;

   vector<vector<T>> centroids;

   for(int i = 0; i < matrix.size(); i++) {
     if (find_if(centroid_indices.begin(), centroid_indices.end(), compare(i)) != centroid_indices.end()) {
       centroids.push_back(matrix.at(i));
     }
   }

   cout << "Matriz inicial de centroides" << endl;
   printMatrix(centroids);


   //K-Means algorithm
   int points_that_converged = 0;
   int iterations = 0;

   while((points_that_converged < centroids.size())) {
     points_that_converged = 0;

     vector<vector<int>> t_hash;
     for(int i = 0; i < centroids.size(); i++) {
       vector<int> v1;
       t_hash.push_back(v1);
     }

     for(int i = 0; i < matrix.size(); i++) {
       vector<T> v = matDistance(centroids, matrix.at(i));
       T mini = v[0];
       int iterationManagement = 0;
       for(int j = 0; j < centroids.size(); j++) {
         if (v[j] < mini) {
           mini = v[j];
           iterationManagement = j;
         }
       }

       t_hash.at(iterationManagement).push_back(i);
     }


     cout << "Iteration " << iterations << endl;
     cout << "---------------------------------------------------------------------------" << endl;
     cout << "Clasification" << endl;
     printMatrix(t_hash);


     for(int i=0; i < t_hash.size(); i++) {

       vector<T> v_means;
       for(int j=0; j < centroids.at(i).size(); j++) {

         T average = 0;
         for(int z=0; z < t_hash.at(i).size(); z++) {
           average += matrix[t_hash[i][z]][j];
         }
         average =  (T)average / centroids.at(i).size();
         if (average == 0) {
           average = centroids[i][j];
           bool sum = 0 + (rand() % (1 - 0 + 1));
           if (sum){
              average += (T)(rand() % 100)/100;
           } else {
             average -= (T)(rand() % 100)/100;
           }

           average = abs(average);

         }
         v_means.push_back(average);

       }

       bool conv = check_convergence(centroids.at(i), v_means);
       if (conv) {
         points_that_converged ++;
         cout << "Converged" << '\n';
       } else {
         centroids.at(i) = v_means;
       }



     }

     cout << "Centroids" << endl;
     printMatrix(centroids);

     iterations ++;
  }

  vector<vector<int>> t_hash;
  for(int i = 0; i < centroids.size(); i++) {
    vector<int> v1;
    t_hash.push_back(v1);
  }

  for(int i = 0; i < matrix.size(); i++) {
    vector<T> v = matDistance(centroids, matrix.at(i));
    T mini = v[0];
    int iterationManagement = 0;
    for(int j = 0; j < centroids.size(); j++) {
      if (v[j] < mini) {
        mini = v[j];
        iterationManagement = j;
      }
    }

    t_hash.at(iterationManagement).push_back(i);
  }
  return t_hash;
}


int main () {

  //vector<vector<double>> m1 = parseCSV();
  vector<vector<double>> m1;
  fillVector(m1, 20, 10);
  printMatrix(m1);

  kmeans(m1);

  //vector<double> res = matDistance(m1, m1[1]);
  //print(res);
  //cout<<endl;
  return 0;
}
