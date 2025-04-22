#include <bits/stdc++.h>
using namespace std;
void moveZerosToEnd(vector<int>& arr, int n) {
    int j = 0; // non zero elements {4 5 0 6 0 0 }  
    for (int i = 0; i < n; i++) {
        if (arr[i] != 0) {   
            swap(arr[i], arr[j]); 
            j++;
        }
    }
    // 1st iteration j=0 i=0 swap (arr[0], arr[0]) j++ , i++  -->{4 5 0 6 0 0 } 
    // 2nd iteration j=1 i=1 swap(arr[1] arr[1]) j++ i++ --> {4 5 0 6 0 0 } 
    // 3rd iteration j=2 i=2 but due arr[i]==0 j remains 2 -->{4 5 0 6 0 0 } 
    // 4th iteration j=2 i=3 swap(arr[3], arr[2]) -->{4 5 6 0 0 0 }    
    for (int i = 0; i < n; i++) {
        cout << arr[i] << " ";
    }
    cout << endl;
}

int main() {
    string input; 
    getline(cin,input);
    stringstream s(input);
    int num;
    vector<int> arr;
    while(s>>num)
    {
         arr.push_back(num);
    }
    moveZerosToEnd(arr, arr.size());

    return 0;
}
